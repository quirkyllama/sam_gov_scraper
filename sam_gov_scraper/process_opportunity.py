from datetime import datetime
import json
import logging
from typing import Dict, List

import requests

from sam_gov_scraper.models import SamContractor, SamContract, SamLink, SamPointOfContact, get_session


logger = logging.getLogger(__name__)

DETAILS_URL = "https://sam.gov/api/prod/opps/v2/opportunities/{id}?random=1737005582919"

LINK_URL = "https://sam.gov/api/prod/opps/v3/opportunities/{id}/resources?random=1737007039047&excludeDeleted=false&withScanResult=false"


# TODO - replace this nonsense with passed in thread state
contracts_added = 0
contract_errors = 0
contract_permission_errors = 0
contracts_skipped = 0

def fetch_opportunity_details(opportunity: int) -> Dict:
    """Fetch opportunity details from SAM.gov API"""
    url = DETAILS_URL.format(id=opportunity)
    response = requests.get(url)
    response.raise_for_status()
    return response.json()

def fetch_opportunity_links(opportunity: int) -> List[Dict]:
    """Fetch opportunity links from SAM.gov API"""
    url = LINK_URL.format(id=opportunity)
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    try:
        return data['_embedded']['opportunityAttachmentList']
    except KeyError:
        # THis appears to be what happens when there are no links?
        return []

def process_opportunity(opportunity: int) -> None:
    """Process a single opportunity"""
    global contract_errors
    global contracts_added
    global contracts_skipped
    global contract_permission_errors
    try:
        contract_fields = {'opportunity_id': opportunity}
        all_data = fetch_opportunity_details(opportunity)
        json_data = all_data['data2']

        links = fetch_opportunity_links(opportunity)
        award = json_data.get('award', {})
        awardee = award.get('awardee')
        with get_session() as session:
            # Check if opportunity already exists
            existing_contract = session.query(SamContract).filter_by(opportunity_id=opportunity).first()
            if existing_contract:
                contracts_skipped += 1
                return
            contract_fields['title'] = json_data.get('title')
            contract_fields['organization_id'] = json_data.get('organizationId')
            contract_fields['solicitation_number'] = json_data.get('solicitationNumber')
            description = all_data['description']
            if len(description) > 0:
                contract_fields['description'] = description[0].get('body')

            contract_fields['contract_award_date'] = award.get('date')
            try:
                contract_fields['contract_amount'] = float(award.get('amount'))
            except:
                amount = None
            
            contract_fields['archived'] = all_data.get('archived')
            contract_fields['cancelled'] = all_data.get('cancelled')
            contract_fields['deleted'] = all_data.get('deleted')
            modified_date = all_data.get('modifiedDate')
            # Some things are missing modifiedDate?
            contract_fields['modified_date'] = datetime.strptime(modified_date, '%Y-%m-%dT%H:%M:%S.%f%z') if modified_date else None
            naics_code = next((x for x in json_data.get('naics', []) if x.get('type') == 'primary'), {})
            contract_fields['naics_code'] = naics_code.get('code')[0] if naics_code.get('code') else None
            
            if awardee:
                contract_fields['contract_award_number'] = award.get('number')

                awardee_id = awardee.get('ueiSAM')
                awardee_name = awardee.get('name')
                if awardee_id:
                    contractor = session.query(SamContractor).filter_by(unique_entity_id=awardee_id).first()
                    if not contractor:
                        contractor = SamContractor(
                            unique_entity_id=awardee_id,
                            name=awardee_name
                        )
                        session.add(contractor)
                        session.flush()
                    contract_fields['contractor_id'] = contractor.id
            contract_fields['raw_xhr_data'] = all_data
        
            contract = SamContract(
                **contract_fields
            )

            session.add(contract)
            # Flush to get the contract id 
            session.flush()
            for attachmentList in links:
                for link in attachmentList['attachments']:
                    link_type = link.get('type')                    
                    link_name = link.get('name')
                    link_attachment_id = link.get('attachmentId')
                    link_resource_id = link.get('resourceId')
                    link_extension = link.get('mimeType')
                    if link.get('type') == 'link':
                        url = link.get('uri')
                    else:
                        url = f"https://sam.gov/api/prod/opps/v3/opportunities/resources/files/{link_resource_id}/download?&token="

                    link = SamLink(
                        attachment_id=link_attachment_id,
                        name=link_name,
                        link_type=link_type,
                        resource_id=link_resource_id,
                        extension=link_extension,
                        contract_id=contract.id,
                        url=url
                    )
                    # logger.info(f"Adding link: {link} {link.get_url()}")
                    session.add(link)
            points_of_contact = json_data.get('pointOfContact', [])
            for poc in points_of_contact:
                point_of_contact = SamPointOfContact(
                    name=poc.get('fullName'),
                    email=poc.get('email'),
                    phone=poc.get('phone'),
                    contact_type=poc.get('type'),
                    contract_id=contract.id
                )
                session.add(point_of_contact) 

            session.commit()
            contracts_added += 1            
            if contracts_added % 100 == 0:
                logger.info(f"Added {contracts_added} contracts with {contract_errors} unknown errors {contract_permission_errors} permission errors and {contracts_skipped} skipped")

            # Print the occassional contract to make sure the data looks correct
            if contracts_added % 500 == 0:
                print_contract(contract)


    except KeyError as e:
        contract_errors += 1
        logger.error(f"KeyError processing opportunity: {e} in {json.dumps(json_data, indent=2)}")
        raise e
    except requests.RequestException as e:
        if e.response.status_code == 401:
            logger.warning(f"Permission denied for {opportunity}")
        contract_permission_errors += 1
    except Exception as e:
        contract_errors += 1
        import traceback
        logger.error(f"Error processing opportunity: {e}\n{traceback.format_exc()}")
        logger.error(f"Error processing opportunity: {e}")
        raise e


def print_contract(contract: SamContract):
    print(f"Contract details:")
    print(f"  ID: {contract.id}")
    print(f"  Opportunity ID: {contract.opportunity_id}")
    print(f"  Solicitation #: {contract.solicitation_number}")
    print(f"  Title: {contract.title}")
    print(f"  Description: {contract.description}")
    print(f"  NAICS Code: {contract.naics_code}")
    print(f"  Organization ID: {contract.organization_id}")
    print(f"  Award Date: {contract.contract_award_date}")
    print(f"  Award Number: {contract.contract_award_number}")
    print(f"  Amount: {contract.contract_amount}")
    print(f"  Modified Date: {contract.modified_date}")
    print(f"  Archived: {contract.archived}")
    print(f"  Cancelled: {contract.cancelled}")
    print(f"  Deleted: {contract.deleted}")
    
    if contract.contractor:
        print(f"  Contractor:")
        print(f"    ID: {contract.contractor.id}")
        print(f"    Name: {contract.contractor.name}")
        print(f"    UEI: {contract.contractor.unique_entity_id}")
        print(f"    Address: {contract.contractor.address}")

    print(f"  Points of Contact:")
    for poc in contract.points_of_contact:
        print(f"    - Name: {poc.name}")
        print(f"      Email: {poc.email}")
        print(f"      Phone: {poc.phone}")
        print(f"      Type: {poc.contact_type}")

    logger.info(f"  Links:")
    for link in contract.links:
        print(f"    - Name: {link.name}")
        print(f"      Attachment ID: {link.attachment_id}")
        print(f"      Resource ID: {link.resource_id}")
        print(f"      Extension: {link.extension}")
        print(f"      URL: {link.url}")
