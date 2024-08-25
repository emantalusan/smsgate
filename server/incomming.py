#
import logging
import requests


from typing import  Dict
from sms import SMS


class processSMS:
    def __init__(self) -> None:
        """
        Create a new processSMS object.
        This class handles the process of incomming SMS.
        """
        self.health_state = "OK"
        self.health_logs = None

        self.l = logging.getLogger("processSMS")


    def process_sms(self, sms: SMS) -> Dict:
        """
        Process incomming SMS.

        @param sms: A SMS object to be precessed.
        @return: Returns True, if the SMS has been processed and accepted. Returns False on error.
        """

        self.l.info(f"[{sms.get_id()}] Processing incomming SMS.")

        for i in range(1, 3):
            api_response = {"success" : False}
            if i > 0:
                self.l.debug(f"[{sms.get_id()}] Processing incomming SMS, again.")

            try:
                self.l.info(f"[{sms.get_id()}] Start processing incomming SMS.")
                api_response = self.sms_checkout(sms)

            except Exception as e:
                self.health_state = "CRITICAL"
                self.health_logs = "An exception occurred: " + str(e)
                self.l.debug(f"[{sms.get_id()}] API connection failed.")
                return api_response

            self.l.info(f"[{sms.get_id()}] Processing incomming SMS was successful.")

            # A successful processing clears the error state
            self.health_state = "OK"
            self.health_logs = None

            return api_response


    def sms_checkout(self, sms: SMS) -> Dict:
        """
        Initiate connection to api.

        @param sms: A SMS object to be precessed.
        @return: Returns JSON object for parsing.
        """

        self.l.info(f"[{sms.get_id()}] Sending SMS via configured API.")

        myModem = sms.get_receiving_modem()
        self.l.info(f"[{myModem.modem_config}] < < < < < < < < < < .")
        

        api_url = "http://127.0.0.1:5000/api"
        api_token = "cGstWjBPU3pMdkljT0kyVUl2RGhkVEdWVmZSU1NlaUdTdG5jZXF3VUU3bjBBaDo="

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": "f'Basic {api_token}'"
        }

        payload = {
            "id" : sms.get_id(),
            "sender" : sms.get_sender(),
            "recipient" : sms.get_recipient(),
            "text" : sms.get_text()
        }

        response = requests.post(api_url, json=payload, headers=headers)
        
        return response.json()

