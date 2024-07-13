TELEMATEL | Synchronizer Odoo-Other System
------------------------------------------
This module allows you to synchronize table data from an external
system with Odoo. This gives us the possibility of having the
desired information replicated in two different systems,
achieving high integrity. This synchronization consists of
sending or receiving the records that were created, modified or
deleted in one of the two systems, be it Odoo or the external system,
and need to be replicated in the other. This process can be carried
out in two modes, by Planned Action (Via Cron) or in Real Time. The
Via Cron mode performs the synchronization at a specific date and
time, allowing us to establish the frequency with which we want it
to be executed. This mode has the advantage that the user does not
intervene at any time in the process, which is activated and executed
automatically.
The Real Time mode is activated when the user makes a creation,
modification or deletion of a record whose table is defined in the
configuration that requires synchronization.

Configuration
=============
    * Settings: The configurations to generate the api key are established in
    if it is used in Real Time mode and if you want to keep the Logs of
    every sync.
    1. Api Key for synchronization: It is the secret key that is used to
        Synchronization in Real Time from the External System to Odoo.
        It is necessary to consume the services (explained later)
        send in the Headers this api key that guarantees the permissions.
    2. Generate Logs: This configuration is for if we want to create a
        record with the data of each synchronization and be able to analyze them.

    * Web Services: The Web Services to consume and send the information
    are defined.
    1. Name: Name of the Web Service.
    2. URL: Url where to obtain the records for a specific type of table.
    3. Needs confirmation: It is checked if it is necessary to confirm to
        the external system that the record was inserted, modified or deleted
        correctly.
    4. Confirmation URL: Url to send the confirmation. In most cases the
        url is the same as the one where the record is received, but it may
        be the case that another is used to confirm, that is why it is this
        field. You always have to put the Url even if it is the same as to
        receive.
    5. Shipping URL: It is similar to the above, in most cases it is the
        same as for obtaining the registration, in case it is different,
        it is established here. If it is the same Url, it must also be
        established. The only case that is left blank is that the
        synchronization is one-way from the External System to Odoo.
    6. Needs authentication: In case the consumption of the Web Service
        requires authentication.
    7. Authentication Mode: There are two modes, User and Password;
        or by Api Key.
    8. If the authentication mode is Api Key, the Api Key field is
        enabled to enter it, in case it is User and Password, these
        fields are enabled.

    * Synchronization models: Here you define the models or tables with
    the fields to be synchronized.
    1. Name: Name of the model or table.
    2. Code: Code to define it, it can be any.
    3. Name fields: Name of the field in the external system.
        Technical name in the table.
    4. Code fields: Same as the Name.
    5. Fields Field type: It is the data type of the field.

    * Synchronization Objects: This is where all the settings for syncing
    are set. One is defined for each model or table. The related WS, which
    has already been configured above, is set. Synchronization mode is also
    set, as well as direction and priority. In addition, the fields of the
    External System are paired with their analog in Odoo.
    1. Name: Name of the Object, it can be anyone, always making reference
        to the Odoo model with the external one to know how to identify it.
    2. Address: There are three options:
    Odoo to External: To send records of this model from Odoo to the
        External System.
    External to Odoo: To receive records from the External System to Odoo.
    Bidirectional: Sent and received from both sides. For this case see the
        Synchronization Priority field which is only visible when the
        direction is bidirectional.
    3. Web Service: The Web Service that we have defined for this model
        is selected.
    4. Synchronization Mode: We define if this model will be synchronized
        by Via Cron or in Real time. It is important to clarify that when
        Real Time is selected, Odoo can only be selected as External address,
        because the Real Time synchronization for the records from the
        External System to Odoo is in another configuration.
        4.1 Synchronization Priority: This field is only visible when the
            synchronization mode is Via Cron. It is defined to establish the
            priority in case there is a record that has been modified both in
            Odoo and in the External System, to define which modification prevails.
    5. Odoo model: The model to be synchronized in Odoo is established.
    6. Odoo Ref field: It is the reference field in Odoo, it will always
        be the external Id field.
    7. Model removed: This field is only visible when the sync mode is
        Via Cron. It must be established if we want the registers deleted
        in Odoo to also be deleted in the External System.
        When establishing it, a single option is listed, that is the
        one we must select.
    8. External Model: We select the External Model homologous to contacts.
        We have already configured this in the Synchronization Models section.
    9. External Ref. Field: It is the reference field in the External System,
        it is among the fields that we define in the Synchronization Model
        for this model. It must be the Id of the record in the External System.
    10. Domain and Limit: This is used if we define a domain of the records
        in Odoo that we want to synchronize. For example. In Odoo,
        in the res.partner model, there are all the contacts, clients,
        companies, etc. If we only wanted to synchronize customers it
        would be [(‘customer’, ‘=’, True)]. The limit is used to define the
        number of records in each synchronization if it is Via Cron mode.
    11. Odoo field: Corresponds to the fields in Odoo that we want to
        synchronize and match with its counterpart. The External ID field
        should never be missing.
    12. External Field: Corresponds to the fields in the External System.
        They are already defined in the Synchronization Model, it only remains
        to pair them.
    13. Reference Field: This is very important, it should only be established
        if the field that we want to synchronize is relational, that is, it
        is One2many, Many2many or Many2one. It is the field by which the
        records are related.
    14. It is a note where it is explained what should be sent in the Header of each
        petition. The previously generated api key and the Content Type must be
        application / json.
    15. Action : It is the action that you want to perform in Odoo, 'Create',
        'Write' or 'Unlink' a record.
    16. Method: It is the method to use in the request, Example:
        POST: requests.request("POST", url, headers=headers, data=payload)
        PUT: requests.request("PUT", url, headers=headers, data=payload)
        DELETE: requests.request("DELETE", url, headers=headers, data=payload)
    17. URL: Address to make the request.
    18. Description: Description to pass parameters or not.
    19. Active: Activate or deactivate the Web Service.


Change control
===============
Here is a history of all the synchronizations that have been made,
showing its traceability.

    1. Traceability: Shows the direction of synchronization.
    2. Type of action: Shows the type of action, Create, Modify or Delete.
    3. External ID: It is the External ID in the record in question.
    4. Odoo ID: Odoo ID of the record in question.
    5. Name: Name of the action.
    6. Title: Name of the record in question.
    7. Origin values: It is a dictionary with the values ​​it receives
        from the origin of that synchronization.
    8. Values ​​to the destination: It is a dictionary with the values ​​
        that are sent to the destination of that synchronization.
    9. Modification Date: Date the record was modified.
    10. Synchronization Date: Date when the synchronization was carried out.
    11. Status: Status of the synchronization, Successful or Failed.
    12. Error Message: It is the message that is thrown if the status
        was Failed.

Structure
=========
The following defines the structure of the calls that the Web Services must
fulfill to receive, confirm and send the data and to perform a correct
synchronization.
    -- Structure in requests in Via Cron mode.
        All requests are made by POST.
        1- Request to receive:
            - It sends:
                {
                    'limit': 15
                }
            - It is expected to receive:
                {
                    # this is the status of response
                    'status': "success, error or failed",
                    'error_message': "Description of error if status is error",
                   # content is a list of the values for each record
                    'content': [
                        {
                            'action': "insert, update or delete",
                    # values not necesary if action is delete
                            'values': {
                                'external_id': 1,
                                'name': "Contact 1"
                            }
                        },
                        {
                            'action': "insert, update or delete",
                            'values': {
                                'external_id': 2,
                                'name': "Contact 2"
                            }
                        }
                    ]
                }

        2- Confirmation request:
            - It sends:
                {
                    # this is the status of response
                    'status': "success, error or failed",
                    'error_message': "Description of error if status is error",
                    'content':  [
                        {
                            # this is the status of record
                            'status': 'failed',
                            'error_message': 'Failed reason',
                            'external_id': 1
                        },
                        {
                            'status': 'success',
                            'error_message': False,
                            'external_id': 2
                        }
                    ]
                }
            - Expected:
                {
                    'status': 'success, failed',
                    'error_message': "Description of error if status is error
                    else False"
                }

        3- Request to send:
            - It sends:
                {
                    'action': 'create, update, delete',
                    # values not necesary if action is delete
                    'values': {
                        'name': 'Contact 3'
                    },
                    'external_id': 2
                }
            - Expected:
                {
                    'status': 'success, failed',
                    'error_message': "Description of error if status is error
                    else False"
                }

    -- Structure in requests in Real Time mode.
        1- Request to create from External to Odoo:
            - Sent from External to Odoo:
                import requests
                url = "http://localhost:8071/sync/CON/create"
                payload={ "name": "Name", "unique_id": 1231}
                headers = {
                  'api_key': 'MGNN4Q4JI6Z3I8J1ROT2F3QK7CESDP16', # api key generado previamente
                  'Content-Type': 'application/json'
                }
                response = requests.request("POST", url, headers=headers, data=payload)
            - Return:
                {
                    "jsonrpc": "2.0",
                    "id": null,
                    "result": {
                        "status": "success", # may be failed
                        "error_message": "" # description of error if status is failed
                    }
                }

        2- Request to modify from External to Odoo:
            - Sent from External to Odoo:
                import requests
                url = "http://localhost:8071/sync/CON/1231"
                payload={"name": "Name of record modified"}
                headers = {
                  'api_key': 'MGNN4Q4JI6Z3I8J1ROT2F3QK7CESDP16',
                  'Content-Type': 'application/json'
                }
                response = requests.request("PUT", url, headers=headers, data=payload)
            - Return:
                {
                 "jsonrpc": "2.0",
                 "id": null,
                 "result": {
                 "status": "success", # may be failed
                 "error_message": "" # description of error if status is failed
                 }
                }

        3- Request to remove from External to Odoo:
            - Sent from External:
                import requests
                url = "http://localhost:8071/sync/CON/1354"
                payload={}
                headers = {
                 'api_key': 'MGNN4Q4JI6Z3I8J1ROT2F3QK7CESDP16'
                }

                response = requests.request("DELETE", url, headers=headers, data=payload)
            - Return:
                {
                 "jsonrpc": "2.0",
                 "id": null,
                 "result": {
                 "status": "success", # may be failed
                 "error_message": "" # description of error if status is failed
                 }
                }

Credits
=======

**Contributors**

* Randy La Rosa Alvarez <rra@wedoo.tech> (Developer)
