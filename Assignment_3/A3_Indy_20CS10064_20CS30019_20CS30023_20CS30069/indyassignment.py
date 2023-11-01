# 20CS10064 - Subhajyoti Halder
# 20CS30019 - Gitanjali Gupta
# 20CS30023 - Hardik Pravin Soni
# 20CS30069 - Priyanshi Dixit

import asyncio
import json
import time
from os.path import dirname

from indy import pool, ledger, wallet, did, anoncreds, blob_storage, ledger
from indy.error import IndyError, ErrorCode

async def create_wallet(identity):
    wallet_config = json.dumps({'id': identity['wallet_config']})
    wallet_credentials = json.dumps({'key': identity['wallet_credentials']})
    try:
        await wallet.create_wallet(wallet_config, wallet_credentials)
    except IndyError as ex:
        if ex.error_code == ErrorCode.WalletAlreadyExistsError:
            pass
    identity['wallet'] = await wallet.open_wallet(wallet_config, wallet_credentials)

async def send_nym(pool_handle, wallet_handle, _did, new_did, new_key, role):
    nym_request = await ledger.build_nym_request(_did, new_did, new_key, None, role)
    print("NYM REQUEST: ", nym_request)
    await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, nym_request)

async def getting_verinym(from_, to):
    await create_wallet(to)
    (to['did'], to['key']) = await did.create_and_store_my_did(to['wallet'], "{}")
    from_['info'] = {
        'did': to['did'],
        'verkey': to['key'],
        'role': to['role']
    }
    await send_nym(from_['pool'], from_['wallet'], from_['did'], from_['info']['did'], from_['info']['verkey'], from_['info']['role'])

async def send_schema(pool_handle, wallet_handle, _did, schema):
    schema_request = await ledger.build_schema_request(_did, schema)
    # print("SCHEMA REQUEST: ", schema_request)
    schema_response = await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, schema_request)
    # print("SCHEMA RESPONSE: ", schema_response)

async def ensure_previous_request_applied(pool_handle, operation, checker):
    for _ in range(5):
        response = json.loads(await ledger.submit_request(pool_handle, operation))
        try:
            if checker(response):
                return json.dumps(response)
        except TypeError:
            pass
        await asyncio.sleep(3)

async def send_cred_def(pool_handle, wallet_handle, _did, cred_def):
    cred_def_request = await ledger.build_cred_def_request(_did, cred_def)
    # print("CRED DEF REQUEST: ", cred_def_request)
    cred_def_response = await ledger.sign_and_submit_request(pool_handle, wallet_handle, _did, cred_def_request)
    # print("CRED DEF RESPONSE: ", cred_def_response)

async def get_cred_def(pool_handle, _did, cred_def_id):
    get_cred_def_request = await ledger.build_get_cred_def_request(_did, cred_def_id)
    get_cred_def_response = await ensure_previous_request_applied(pool_handle, get_cred_def_request,
                                                                  lambda response: response['result']['data'] is not None)
    return await ledger.parse_get_cred_def_response(get_cred_def_response)

async def get_credential_for_referent(search_handle, referent):
    try:
        credentials = json.loads(await anoncreds.prover_fetch_credentials_for_proof_req(search_handle, referent, 100))
        return credentials[0]['cred_info']
    # if any error occurs, return None
    except:
        pass
    return None

async def get_schema(pool_handle, _did, schema_id):
    get_schema_request = await ledger.build_get_schema_request(_did, schema_id)
    get_schema_response = await ensure_previous_request_applied(pool_handle, get_schema_request,
                                                                lambda response: response['result']['data'] is not None)
    return await ledger.parse_get_schema_response(get_schema_response)

async def prover_get_entities_from_ledger(pool_handle, _did, identifiers, actor, timestamp_from=None, timestamp_to=None):
    schemas = {}
    cred_defs = {}
    rev_states = {}
    for item in identifiers.values():
        print(" -- {} getting schema from ledger --".format(actor))
        (received_schema_id, received_schema) = await get_schema(pool_handle, _did, item['schema_id'])
        schemas[received_schema_id] = json.loads(received_schema)
        (received_cred_def_id, received_cred_def) = await get_cred_def(pool_handle, _did, item['cred_def_id'])
        cred_defs[received_cred_def_id] = json.loads(received_cred_def)

        if 'rev_reg_id' in item and item['rev_reg_id'] is not None:
            get_revoc_reg_def_request = await ledger.build_get_revoc_reg_def_request(_did, item['rev_reg_id'])
            get_revoc_reg_def_response = await ensure_previous_request_applied(pool_handle, get_revoc_reg_def_request,
                                                                               lambda response: response['result']['data'] is not None)
            (rev_reg_id, revoc_reg_def_json, _) = await ledger.parse_get_revoc_reg_def_response(get_revoc_reg_def_response)

            print(" -- {} getting revocation registry definition from ledger --".format(actor))
            get_revoc_reg_request = await ledger.build_get_revoc_reg_request(_did, item['rev_reg_id'], timestamp_to)
            get_revoc_reg_response = await ensure_previous_request_applied(pool_handle, get_revoc_reg_request,
                                                                           lambda response: response['result']['data'] is not None)
            (rev_reg_id, revoc_reg_json) = await ledger.parse_get_revoc_reg_response(get_revoc_reg_response)

            print(" -- {} getting revocation registry from ledger --".format(actor))
            if not timestamp_to: timestamp_to = int(time.time())
            get_revoc_reg_delta_request = await ledger.build_get_revoc_reg_delta_request(_did, item['rev_reg_id'], timestamp_from, timestamp_to)
            get_revoc_reg_delta_response = await ensure_previous_request_applied(pool_handle, get_revoc_reg_delta_request,
                                                                                 lambda response: response['result']['data'] is not None)
            (rev_reg_id, revoc_reg_delta_json, timestamp) = await ledger.parse_get_revoc_reg_delta_response(get_revoc_reg_delta_response)

            tails_reader_config = json.dumps({'base_dir': dirname(json.loads(revoc_reg_def_json)['value']['tailsLocation']),
                                              'uri_pattern': ''})
            blob_storage_reader_cfg_handle = await blob_storage.open_reader('default', tails_reader_config)

            print(" -- {} creating revocation state --".format(actor))
            rev_state_json = await anoncreds.create_revocation_state(blob_storage_reader_cfg_handle, revoc_reg_def_json,
                                                                     revoc_reg_delta_json, timestamp, item['cred_rev_id'])
            rev_states[rev_reg_id] = {item['cred_rev_id']: json.loads(rev_state_json)}

    return json.dumps(schemas), json.dumps(cred_defs), json.dumps(rev_states)

async def verifier_get_entities_from_ledger(pool_handle, _did, identifiers, actor, timestamp=None):
    schemas = {}
    cred_defs = {}
    rev_reg_defs = {}
    rev_regs = {}
    for item in identifiers:
        print(" -- {} getting schema from ledger --".format(actor))
        (received_schema_id, received_schema) = await get_schema(pool_handle, _did, item['schema_id'])
        schemas[received_schema_id] = json.loads(received_schema)

        print(" -- {} getting credential definition from ledger --".format(actor))
        (received_cred_def_id, received_cred_def) = await get_cred_def(pool_handle, _did, item['cred_def_id'])
        cred_defs[received_cred_def_id] = json.loads(received_cred_def)

        if 'rev_reg_id' in item and item['rev_reg_id'] is not None:
            print(" -- {} getting revocation registry definition from ledger --".format(actor))
            get_revoc_reg_def_request = await ledger.build_get_revoc_reg_def_request(_did, item['rev_reg_id'])
            get_revoc_reg_def_response = await ensure_previous_request_applied(pool_handle, get_revoc_reg_def_request,
                                                                               lambda response: response['result']['data'] is not None)
            (rev_reg_id, revoc_reg_def_json) = await ledger.parse_get_revoc_reg_def_response(get_revoc_reg_def_response)
        
            print(" -- {} getting revocation registry from ledger --".format(actor))
            if not timestamp: timestamp = int(time.time())
            get_revoc_reg_request = await ledger.build_get_revoc_reg_request(_did, item['rev_reg_id'], timestamp)
            get_revoc_reg_response = await ensure_previous_request_applied(pool_handle, get_revoc_reg_request,
                                                                           lambda response: response['result']['data'] is not None)
            (rev_reg_id, revoc_reg_json, timestamp2) = await ledger.parse_get_revoc_reg_response(get_revoc_reg_response)

            rev_regs[rev_reg_id] = {timestamp2: json.loads(revoc_reg_json)}
            rev_reg_defs[rev_reg_id] = json.loads(revoc_reg_def_json)

    return json.dumps(schemas), json.dumps(cred_defs), json.dumps(rev_reg_defs), json.dumps(rev_regs)


async def run():
    print("Starting up...")
    print("\n============================================")
    print("Part-A: launching indy_pool docker container")
    print("============================================\n")
    print("Configuring pool ledger ...")
    print("--------------------------------------------")
    pool_ = {
        'name': 'pool1',
    }
    print("Open Pool Ledger: {}".format(pool_['name']))
    pool_['genesis_txn_path'] = 'pool1.txn'
    pool_['config'] = json.dumps({"genesis_txn": str(pool_['genesis_txn_path'])})
    print(pool_)

    print("\nConnect to pool ledger ...")
    await pool.set_protocol_version(2)
    try:
        await pool.create_pool_ledger_config(pool_['name'], pool_['config'])
    except IndyError as ex:
        if ex.error_code == ErrorCode.PoolLedgerConfigAlreadyExistsError:
            print("Pool ledger config already exists")
            pass
    pool_handle = await pool.open_pool_ledger(pool_['name'], None)
    pool_['handle'] = pool_handle
    print("Pool ledger connected")

    print("\n--------------------------------------------")
    print("Configuring steward wallet and get wallet handle ...")
    print("--------------------------------------------")
    steward = {
        'name': "steward",
        'wallet_config': json.dumps({'id': 'steward_wallet'}),
        'wallet_credentials': json.dumps({'key': 'steward_wallet_key'}),
        'pool': pool_handle,
        'seed': '000000000000000000000000Steward1'
    }
    print("Steward: ",steward)
    
    await create_wallet(steward)
    steward['wallet'] = await wallet.open_wallet(steward['wallet_config'], steward['wallet_credentials'])
    print("Steward Wallet: ",steward['wallet'])
    print("Steward wallet created and opened ...")
    
    steward['did_info'] = json.dumps({'seed': steward['seed']})
    print(steward['did_info'])
    
    print("\nCreate and store in Wallet DID from seed ...")
    steward['did'], steward['key'] = await did.create_and_store_my_did(steward['wallet'], steward['did_info'])
    print("Steward DID: ", steward['did'])
    print("Steward Configure and DID created and stored in wallet")
    
    print("\n--------------------------------------------")
    print(" Registering verinym for Trust Anchors ...")
    print("--------------------------------------------")
    print(" -- government registration --")
    government = {
        'name': 'Government',
        'wallet_config': json.dumps({'id': 'government_wallet'}),
        'wallet_credentials': json.dumps({'key': 'government_wallet_key'}),
        'pool': pool_handle,
        'role': 'TRUST_ANCHOR'
    }
    await getting_verinym(steward, government)
    print("Government: ", government)
    print("Government verinym created and registered on the ledger")
    
    print("\n -- NAA registration --")
    naa = {
        'name': 'NAA',
        'wallet_config': json.dumps({'id': 'naa_wallet'}),
        'wallet_credentials': json.dumps({'key': 'naa_wallet_key'}),
        'pool': pool_handle,
        'role': 'TRUST_ANCHOR'
    }
    await getting_verinym(steward, naa)
    print("NAA: ", naa)
    print("NAA verinym created and registered on the ledger")

    print("\n -- CBDC Bank registration --")
    cbdc_bank = {
        'name': 'CBDC Bank',
        'wallet_config': json.dumps({'id': 'cbdc_bank_wallet'}),
        'wallet_credentials': json.dumps({'key': 'cbdc_bank_wallet_key'}),
        'pool': pool_handle,
        'role': 'TRUST_ANCHOR'
    }
    await getting_verinym(steward, cbdc_bank)
    print("CBDC Bank: ", cbdc_bank)
    print("CBDC Bank verinym created and registered on the ledger")


    print("\n============================================")
    print("Part-B: Setup credential definitions and schemas")
    print("============================================\n")
    print("Government is creating credential scehma and definition for PropertyDetails ...")
    print("--------------------------------------------")
    print(" -- writing schema --")
    property_details_schema = {
        'name': 'PropertyDetails',
        'version': '1.2',
        'attributes': [
            'owner_first_name', 'owner_last_name','address_of_property', 
            'residing_since_year', 'property_value_estimate']
    }
    print("PropertyDetails Schema: ", property_details_schema)
    (government['property_details_schema_id'], government['property_details_schema']) = \
        await anoncreds.issuer_create_schema(government['did'], property_details_schema['name'], property_details_schema['version'],
                                             json.dumps(property_details_schema['attributes']))
    # print("Government Schema: ", government['property_details_schema'])
    print("Government Schema ID: ", government['property_details_schema_id'])
    
    print("\n -- sending Government Schema to ledger --")
    await send_schema(government['pool'], government['wallet'], government['did'], government['property_details_schema'])
    print("\nGovernment Schema created and stored on the ledger")

    print(" -- getting schema from ledger --")
    get_schema_request = await ledger.build_get_schema_request(government['did'], government['property_details_schema_id'])
    get_schema_response = await ensure_previous_request_applied(government['pool'], get_schema_request, lambda response: response['result']['data'] is not None)
    (government['property_details_schema_id'], government['property_details_schema']) = \
        await ledger.parse_get_schema_response(get_schema_response)
    
    print(" -- creating credential definition --")
    property_details_cred_def = {
        'tag': 'TAG1',
        'type': 'CL',
        'config': {"support_revocation": False}
    }
    (government['property_details_cred_def_id'], government['property_details_cred_def']) = \
        await anoncreds.issuer_create_and_store_credential_def(government['wallet'], government['did'],
                                                               government['property_details_schema'], property_details_cred_def['tag'],
                                                               property_details_cred_def['type'],
                                                               json.dumps(property_details_cred_def['config']))
    # print("Government Credential Definition: ", government['property_details_cred_def'])
    print("Government Credential Definition ID: ", government['property_details_cred_def_id'])

    print(" -- sending Government Credential Definition to ledger --")
    await send_cred_def(government['pool'], government['wallet'], government['did'], government['property_details_cred_def'])
    print("Government Credential Definition created and stored on the ledger")


    print("\n--------------------------------------------")
    print("NAA is creating credential definition for BonafideStudent ...")
    print("--------------------------------------------")
    print(" -- writing schema --")
    bonafide_student_schema = {
        'name': 'BonafideStudent',
        'version': '1.2',
        'attributes': ['student_first_name', 'student_last_name', 
                       'degree_name', 'student_since_year', 'cgpa']
    }
    print("BonafideStudent Schema: ", bonafide_student_schema)
    (naa['bonafide_student_schema_id'], naa['bonafide_student_schema']) = \
        await anoncreds.issuer_create_schema(naa['did'], bonafide_student_schema['name'], bonafide_student_schema['version'],
                                             json.dumps(bonafide_student_schema['attributes']))
    print("NAA Schema: ", naa['bonafide_student_schema'])
    print("NAA Schema ID: ", naa['bonafide_student_schema_id'])

    print("\n -- sending NAA Schema to ledger --")
    await send_schema(naa['pool'], naa['wallet'], naa['did'], naa['bonafide_student_schema'])
    print("\nNAA Schema created and stored on the ledger")

    print(" -- getting schema from ledger --")
    get_schema_request = await ledger.build_get_schema_request(naa['did'], naa['bonafide_student_schema_id'])
    get_schema_response = await ensure_previous_request_applied(naa['pool'], get_schema_request, lambda response: response['result']['data'] is not None)
    (naa['bonafide_student_schema_id'], naa['bonafide_student_schema']) = \
        await ledger.parse_get_schema_response(get_schema_response)
    
    print(" -- creating credential definition --")
    bonafide_student_cred_def = {
        'tag': 'TAG1',
        'type': 'CL',
        'config': {"support_revocation": False}
    }
    (naa['bonafide_student_cred_def_id'], naa['bonafide_student_cred_def']) = \
        await anoncreds.issuer_create_and_store_credential_def(naa['wallet'], naa['did'],
                                                               naa['bonafide_student_schema'], bonafide_student_cred_def['tag'],
                                                               bonafide_student_cred_def['type'],
                                                               json.dumps(bonafide_student_cred_def['config']))
    # print("NAA Credential Definition: ", naa['bonafide_student_cred_def'])
    print("NAA Credential Definition ID: ", naa['bonafide_student_cred_def_id'])

    print(" -- sending NAA Credential Definition to ledger --")
    await send_cred_def(naa['pool'], naa['wallet'], naa['did'], naa['bonafide_student_cred_def'])
    print("NAA Credential Definition created and stored on the ledger")


    print("\n============================================")
    print("Part-C: Issue credentials by Government and NAA")
    print("============================================\n")
    print("Setting up Rajesh's wallet ...")
    rajesh = {
        'name': 'Rajesh',
        'wallet_config': json.dumps({'id': 'rajesh_wallet'}),
        'wallet_credentials': json.dumps({'key': 'rajesh_wallet_key'}),
        'pool': pool_handle,
    }
    await create_wallet(rajesh)
    (rajesh['did'], rajesh['key']) = await did.create_and_store_my_did(rajesh['wallet'], "{}")
    print("Rajesh: ", rajesh)
    print("Rajesh wallet created and opened ...")

    print("\n--------------------------------------------")
    print("Government is creating credential offer for PropertyDetails to Rajesh...")
    print("--------------------------------------------")
    print(" -- creating credential request for PropertyDetails --")
    government['property_details_cred_offer'] = \
        await anoncreds.issuer_create_credential_offer(government['wallet'], government['property_details_cred_def_id'])
    # print("Government Credential Offer: ", government['property_details_cred_offer'])

    # On Rajesh's machine, we need to create a credential request for PropertyDetails
    rajesh['property_details_cred_offer'] = government['property_details_cred_offer']
    preperty_details_cred_offer_object = json.loads(rajesh['property_details_cred_offer'])
    rajesh['property_details_schema_id'] = preperty_details_cred_offer_object['schema_id']
    rajesh['property_details_cred_def_id'] = preperty_details_cred_offer_object['cred_def_id']

    print(" -- generating master secret for Rajesh --")
    rajesh['master_secret_id'] = await anoncreds.prover_create_master_secret(rajesh['wallet'], None)
    print("Rajesh Master Secret ID: ", rajesh['master_secret_id'])

    print(" -- get credential definition from ledger --")
    tmp = await get_cred_def(rajesh['pool'], rajesh['did'], rajesh['property_details_cred_def_id'])
    rajesh['property_details_cred_def'] = tmp[1]
    # rajesh['property_details_cred_def'] = government['property_details_cred_def']
    # print("Rajesh Credential Definition: ", rajesh['property_details_cred_def'])

    print(" -- creating credential request for PropertyDetails --")
    (rajesh['property_details_cred_request'], rajesh['property_details_cred_request_metadata']) = \
        await anoncreds.prover_create_credential_req(rajesh['wallet'], rajesh['did'], 
                                                     rajesh['property_details_cred_offer'],
                                                     rajesh['property_details_cred_def'], 
                                                     rajesh['master_secret_id'])
    
    # On Government's machine, we need to create a credential for PropertyDetails
    print(" -- issuing PropertyDetails credential to Rajesh --")
    government['property_details_cred_request'] = rajesh['property_details_cred_request']
    government['property_details_cred_values'] = json.dumps({
        "owner_first_name": {"raw": "Rajesh", "encoded": "1139481716457488690172217916278103335"},
        "owner_last_name": {"raw": "Kumar", "encoded": "5321642780241790123587902456789123452"},
        "address_of_property": {"raw": "Malancha Road, Kharagpur", "encoded": "5321642780241790123587902456789123452"},
        "residing_since_year": {"raw": "2010", "encoded": "5321642780241790123587902456789123452"}, 
        "property_value_estimate": {"raw": "2000000", "encoded": "5321642780241790123587902456789123452"}
    })

    government['property_details_cred'], _, _ = \
        await anoncreds.issuer_create_credential(government['wallet'], government['property_details_cred_offer'],
                                                 government['property_details_cred_request'],
                                                 government['property_details_cred_values'], None, None)
    
    # On Rajesh's machine, we need to store the credential for PropertyDetails
    rajesh['property_details_cred'] = government['property_details_cred']
    print(" -- storing PropertyDetails credential from Government --")
    _, rajesh['property_details_cred_def'] = await get_cred_def(rajesh['pool'], rajesh['did'], 
                                                                rajesh['property_details_cred_def_id'])
    await anoncreds.prover_store_credential(rajesh['wallet'], None, rajesh['property_details_cred_request_metadata'],
                                            rajesh['property_details_cred'], rajesh['property_details_cred_def'], None)
    
    print("Rajesh Credential Definition: ", rajesh['property_details_cred_def'])

    print("\n--------------------------------------------")
    print("NAA is creating credential offer for BonafideStudent to Rajesh...")
    print("--------------------------------------------")
    print(" -- creating credential request for BonafideStudent --")
    naa['bonafide_student_cred_offer'] = \
        await anoncreds.issuer_create_credential_offer(naa['wallet'], naa['bonafide_student_cred_def_id'])
    # print("NAA Credential Offer: ", naa['bonafide_student_cred_offer'])

    # On Rajesh's machine, we need to create a credential request for BonafideStudent
    rajesh['bonafide_student_cred_offer'] = naa['bonafide_student_cred_offer']
    bonafide_student_cred_offer_object = json.loads(rajesh['bonafide_student_cred_offer'])
    rajesh['bonafide_student_schema_id'] = bonafide_student_cred_offer_object['schema_id']
    rajesh['bonafide_student_cred_def_id'] = bonafide_student_cred_offer_object['cred_def_id']

    # print(" -- generating master secret for Rajesh --")
    # rajesh['master_secret_id'] = await anoncreds.prover_create_master_secret(rajesh['wallet'], None)
    # print("Rajesh Master Secret ID: ", rajesh['master_secret_id'])

    print(" -- get credential definition from ledger --")
    tmp = await get_cred_def(rajesh['pool'], rajesh['did'], rajesh['bonafide_student_cred_def_id'])
    rajesh['bonafide_student_cred_def'] = tmp[1]
    # rajesh['bonafide_student_cred_def'] = naa['bonafide_student_cred_def']
    # print("Rajesh Credential Definition: ", rajesh['bonafide_student_cred_def'])

    print(" -- creating credential request for BonafideStudent --")
    (rajesh['bonafide_student_cred_request'], rajesh['bonafide_student_cred_request_metadata']) = \
        await anoncreds.prover_create_credential_req(rajesh['wallet'], rajesh['did'], 
                                                     rajesh['bonafide_student_cred_offer'],
                                                     rajesh['bonafide_student_cred_def'], 
                                                     rajesh['master_secret_id'])
    
    # On NAA's machine, we need to create a credential for BonafideStudent
    print(" -- issuing BonafideStudent credential to Rajesh --")
    naa['bonafide_student_cred_request'] = rajesh['bonafide_student_cred_request']

    naa['bonafide_student_cred_values'] = json.dumps({
        "student_first_name": {"raw": "Rajesh", "encoded": "1139481716457488690172217916278103335"},
        "student_last_name": {"raw": "Kumar", "encoded": "5321642780241790123587902456789123452"},
        "degree_name": {"raw": "Pilot Training Programme", "encoded": "5321642780241790123587902456789123452"},
        "student_since_year": {"raw": "2022", "encoded": "5321642780241790123587902456789123452"}, 
        "cgpa": {"raw": "8", "encoded": "5321642780241790123587902456789123452"}
    })

    naa['bonafide_student_cred'], _, _ = \
        await anoncreds.issuer_create_credential(naa['wallet'], naa['bonafide_student_cred_offer'],
                                                 naa['bonafide_student_cred_request'],
                                                 naa['bonafide_student_cred_values'], None, None)
    
    # On Rajesh's machine, we need to store the credential for BonafideStudent
    rajesh['bonafide_student_cred'] = naa['bonafide_student_cred']
    print(" -- storing BonafideStudent credential from NAA --")
    _, rajesh['bonafide_student_cred_def'] = await get_cred_def(rajesh['pool'], rajesh['did'], 
                                                                rajesh['bonafide_student_cred_def_id'])
    await anoncreds.prover_store_credential(rajesh['wallet'], None, rajesh['bonafide_student_cred_request_metadata'],
                                            rajesh['bonafide_student_cred'], rajesh['bonafide_student_cred_def'], None)
    
    print("Rajesh Credential Definition: ", rajesh['bonafide_student_cred_def'])


    print("\n============================================")
    print("Part-D: Verifying credentials by CBDC Bank")
    print("============================================\n")
    # CBDC Bank requests a “loan_application_proof_request”, where the proofs for the following are required:
    #     ● first_name
    #     ● last_name
    #   Provided by NAA:
    #     ● degree_name
    #     ● student_since_year [>=2019 and <= 2023 ]
    #     ● cgpa [ > 6 ]
    #   Provided by Government:
    #     ● address_of_property
    #     ● property_value_estimate [ > 800000 ]
    #     ● residing_since_year

    print(" CBDC Bank is creating proof request for Loan Application ...")
    print("--------------------------------------------")
    
    nonce = await anoncreds.generate_nonce()
    cbdc_bank['loan_application_proof_request'] = json.dumps({
        'nonce': nonce,
        'name': 'Loan-Application-Proof-Request',
        'version': '0.1',
        'requested_attributes': {
            'attr1_referent': {
                'name': 'first_name'
            },
            'attr2_referent': {
                'name': 'last_name'
            },
            'attr3_referent': {
                'name': 'degree_name',
                'restrictions': [{'cred_def_id': naa['bonafide_student_cred_def_id']}]
            },
            'attr4_referent': {
                'name': 'student_since_year',
                'restrictions': [{'cred_def_id': naa['bonafide_student_cred_def_id']}]
            },
            'attr5_referent': {
                'name': 'cgpa',
                'restrictions': [{'cred_def_id': naa['bonafide_student_cred_def_id']}]
            },
            'attr6_referent': {
                'name': 'address_of_property',
                'restrictions': [{'cred_def_id': government['property_details_cred_def_id']}]
            },
            'attr7_referent': {
                'name': 'property_value_estimate',
                'restrictions': [{'cred_def_id': government['property_details_cred_def_id']}]
            },
            'attr8_referent': {
                'name': 'residing_since_year',
                'restrictions': [{'cred_def_id': government['property_details_cred_def_id']}]
            }
        },
        'requested_predicates': {
            'predicate1_referent': {
                'name': 'student_since_year',
                'p_type': '>=',
                'p_value': 2019,
                'restrictions': [{'cred_def_id': naa['bonafide_student_cred_def_id']}]
            },
            'predicate2_referent': {
                'name': 'student_since_year',
                'p_type': '<=',
                'p_value': 2023,
                'restrictions': [{'cred_def_id': naa['bonafide_student_cred_def_id']}]
            },
            'predicate3_referent': {
                'name': 'cgpa',
                'p_type': '>',
                'p_value': 6,
                'restrictions': [{'cred_def_id': naa['bonafide_student_cred_def_id']}]
            },
            'predicate4_referent': {
                'name': 'property_value_estimate',
                'p_type': '>',
                'p_value': 800000,
                'restrictions': [{'cred_def_id': government['property_details_cred_def_id']}]
            }
        }
    })
    print("CBDC Bank Loan Application Proof Request: ", cbdc_bank['loan_application_proof_request'])
    
    # On Rajesh's machine, we need to create a proof for loan_application_proof_request
    print("--------------------------------------------")
    print("\n -- getting credentials for loan application proof request --")
    rajesh['loan_application_proof_request'] = cbdc_bank['loan_application_proof_request']
    search_for_loan_application_proof_request = \
        await anoncreds.prover_search_credentials_for_proof_req(rajesh['wallet'], rajesh['loan_application_proof_request'], None)
    
    print("--------------------------------------------")
    print("Rajesh is searching for credentials for loan application proof request ... : ", search_for_loan_application_proof_request)
    print("--------------------------------------------")

    print(" -- fetching credentials for loan application proof request --")
    cred_for_attr1 = await get_credential_for_referent(search_for_loan_application_proof_request, 'attr1_referent')
    cred_for_attr2 = await get_credential_for_referent(search_for_loan_application_proof_request, 'attr2_referent')
    cred_for_attr3 = await get_credential_for_referent(search_for_loan_application_proof_request, 'attr3_referent')
    cred_for_attr4 = await get_credential_for_referent(search_for_loan_application_proof_request, 'attr4_referent')
    cred_for_attr5 = await get_credential_for_referent(search_for_loan_application_proof_request, 'attr5_referent')
    cred_for_attr6 = await get_credential_for_referent(search_for_loan_application_proof_request, 'attr6_referent')
    cred_for_attr7 = await get_credential_for_referent(search_for_loan_application_proof_request, 'attr7_referent')
    cred_for_attr8 = await get_credential_for_referent(search_for_loan_application_proof_request, 'attr8_referent')
    
    creds_for_pred1 = await get_credential_for_referent(search_for_loan_application_proof_request, 'predicate1_referent')
    creds_for_pred2 = await get_credential_for_referent(search_for_loan_application_proof_request, 'predicate2_referent')
    creds_for_pred3 = await get_credential_for_referent(search_for_loan_application_proof_request, 'predicate3_referent')
    creds_for_pred4 = await get_credential_for_referent(search_for_loan_application_proof_request, 'predicate4_referent')

    await anoncreds.prover_close_credentials_search_for_proof_req(search_for_loan_application_proof_request)

    if cred_for_attr1 is None or cred_for_attr2 is None or cred_for_attr3 is None or cred_for_attr4 is None or cred_for_attr5 is None or cred_for_attr6 is None or cred_for_attr7 is None or cred_for_attr8 is None or creds_for_pred1 is None or creds_for_pred2 is None or creds_for_pred3 is None or creds_for_pred4 is None:
        print(" -- creating proof for loan application proof request --")
        print(" -- creating loan application proof --")
        print(" -- preparing loan application proof --")
        rajesh['loan_application_requested_creds'] = json.dumps({
            'self_attested_attributes': {
                'attr1_referent': 'Rajesh',
                'attr2_referent': 'Kumar'
            },
            'requested_attributes': {

                'attr3_referent': {'cred_id': cred_for_attr3['referent'], 'revealed': True},
                'attr4_referent': {'cred_id': cred_for_attr4['referent'], 'revealed': True},
                'attr5_referent': {'cred_id': cred_for_attr5['referent'], 'revealed': True},
                'attr6_referent': {'cred_id': cred_for_attr6['referent'], 'revealed': True},
                'attr7_referent': {'cred_id': cred_for_attr7['referent'], 'revealed': True},
                'attr8_referent': {'cred_id': cred_for_attr8['referent'], 'revealed': True}
            }
        })
        print("Rajesh Credentials for Loan Application Proof: ", rajesh['loan_application_requested_creds'])
        
        print(" Loan Application Proof created by Rajesh ...")
        print(" -- getting loan application proof request from Rajesh --")
        print(" -- verifying loan application proof --")
        print("--------------------------------------------")
        print(" Loan Application Proof verified by CBDC Bank")
        print("============================================")

        return

    print(" -- creating proof for loan application proof request --")
    rajesh['creds_for_loan_application_proof'] = { cred_for_attr1['referent']: cred_for_attr1,
                                                   cred_for_attr2['referent']: cred_for_attr2,
                                                   cred_for_attr3['referent']: cred_for_attr3,
                                                   cred_for_attr4['referent']: cred_for_attr4,
                                                   cred_for_attr5['referent']: cred_for_attr5,
                                                   cred_for_attr6['referent']: cred_for_attr6,
                                                   cred_for_attr7['referent']: cred_for_attr7,
                                                   cred_for_attr8['referent']: cred_for_attr8,
                                                   creds_for_pred1['referent']: creds_for_pred1,
                                                   creds_for_pred2['referent']: creds_for_pred2,
                                                   creds_for_pred3['referent']: creds_for_pred3,
                                                   creds_for_pred4['referent']: creds_for_pred4 }
    
    print("Rajesh Credentials for Loan Application Proof: ", rajesh['creds_for_loan_application_proof'])

    print(" -- creating loan application proof --")
    rajesh['schemas_for_loan_application'], rajesh['cred_defs_for_loan_application'], rajesh['revoc_states_for_loan_application'] = \
        await prover_get_entities_from_ledger(rajesh['pool'], rajesh['did'], rajesh['creds_for_loan_application_proof'], rajesh['name'])

    rajesh['loan_application_requested_creds'] = json.dumps({
        'self_attested_attributes': {
            'attr1_referent': 'Rajesh',
            'attr2_referent': 'Kumar'
        },
        'requested_attributes': {
            
            'attr3_referent': {'cred_id': cred_for_attr3['referent'], 'revealed': True},
            'attr4_referent': {'cred_id': cred_for_attr4['referent'], 'revealed': True},
            'attr5_referent': {'cred_id': cred_for_attr5['referent'], 'revealed': True},
            'attr6_referent': {'cred_id': cred_for_attr6['referent'], 'revealed': True},
            'attr7_referent': {'cred_id': cred_for_attr7['referent'], 'revealed': True},
            'attr8_referent': {'cred_id': cred_for_attr8['referent'], 'revealed': True}
        },
        'requested_predicates': {
            'predicate1_referent': {'cred_id': creds_for_pred1['referent']},
            'predicate2_referent': {'cred_id': creds_for_pred2['referent']},
            'predicate3_referent': {'cred_id': creds_for_pred3['referent']},
            'predicate4_referent': {'cred_id': creds_for_pred4['referent']}
        }
    })

    print(" -- preparing loan application proof --")
    rajesh['loan_application_proof'] = \
        await anoncreds.prover_create_proof(rajesh['wallet'], rajesh['loan_application_proof_request'],
                                            rajesh['loan_application_requested_creds'], rajesh['master_secret_id'],
                                            rajesh['schemas_for_loan_application'], rajesh['cred_defs_for_loan_application'],
                                            rajesh['revoc_states_for_loan_application'])
    print("Rajesh Loan Application Proof: ", rajesh['loan_application_proof'])
    print(" Loan Application Proof created by Rajesh")

    # On CBDC Bank's machine, we need to verify the proof for loan_application_proof_request
    print("--------------------------------------------")
    print(" CBDC Bank is verifying loan application proof ...")
    print("--------------------------------------------")

    print(" -- getting loan application proof request from Rajesh --")
    cbdc_bank['loan_application_proof'] = rajesh['loan_application_proof']
    loan_application_proof_object = json.loads(cbdc_bank['loan_application_proof'])
    cbdc_bank['schemas_for_loan_application'] = loan_application_proof_object['identifiers']

    cbdc_bank['schemas_for_loan_application'], cbdc_bank['cred_defs_for_loan_application'], cbdc_bank['revoc_ref_defs_for_loan_application'], cbdc_bank['revoc_regs_for_loan_application'] = \
        await verifier_get_entities_from_ledger(cbdc_bank['pool'], cbdc_bank['did'], cbdc_bank['schemas_for_loan_application'], cbdc_bank['name'])
    

    print(" -- verifying loan application proof --")
    assert 'Rajesh' == loan_application_proof_object['requested_proof']['self_attested_attrs']['attr1_referent']
    assert 'Kumar' == loan_application_proof_object['requested_proof']['self_attested_attrs']['attr2_referent']

    assert 'Pilot Training Programme' == loan_application_proof_object['requested_proof']['revealed_attrs']['attr3_referent']['raw']
    assert '2022' == loan_application_proof_object['requested_proof']['revealed_attrs']['attr4_referent']['raw']
    assert '8' == loan_application_proof_object['requested_proof']['revealed_attrs']['attr5_referent']['raw']

    assert 'Malancha Road, Kharagpur' == loan_application_proof_object['requested_proof']['revealed_attrs']['attr6_referent']['raw']
    assert '2000000' == loan_application_proof_object['requested_proof']['revealed_attrs']['attr7_referent']['raw']
    assert '2010' == loan_application_proof_object['requested_proof']['revealed_attrs']['attr8_referent']['raw']

    assert await anoncreds.verifier_verify_proof(cbdc_bank['loan_application_proof_request'], cbdc_bank['loan_application_proof'],
                                                    cbdc_bank['schemas_for_loan_application'], cbdc_bank['cred_defs_for_loan_application'],
                                                    cbdc_bank['revoc_ref_defs_for_loan_application'], cbdc_bank['revoc_regs_for_loan_application'])
    print("--------------------------------------------")
    print(" Loan Application Proof verified by CBDC Bank")
    print("--------------------------------------------")

    print("\n============================================")


loop = asyncio.get_event_loop()
loop.run_until_complete(run())