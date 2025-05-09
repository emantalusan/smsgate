# -----------------------------------------------------------------------------
# Copyright (c) 2022 Martin Schobert, Pentagrid AG
#
# All rights reserved.
#
#  Redistribution and use in source and binary forms, with or without
#  modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
#  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
#  ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
#  WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
#  DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
#  ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
#  (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
#  LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
#  ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
#  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
#  SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
#  The views and conclusions contained in the software and documentation are those
#  of the authors and should not be interpreted as representing official policies,
#  either expressed or implied, of the project.
#
#  NON-MILITARY-USAGE CLAUSE
#  Redistribution and use in source and binary form for military use and
#  military research is not permitted. Infringement of these clauses may
#  result in publishing the source code of the utilizing applications and
#  libraries to the public. As this software is developed, tested and
#  reviewed by *international* volunteers, this clause shall not be refused
#  due to the matter of *national* security concerns.
# -----------------------------------------------------------------------------

import datetime
import logging
import requests
from typing import Tuple
from sms import SMS

class APIDelivery:
    def __init__(
        self, url: str, token: str, health_check_interval: int
    ) -> None:
        """
        Create a new APIDelivery object.
        This class handles the delivery of SMS via an HTTP API and supports health checks.

        @param url: The API endpoint URL.
        @param token: The authorization token for the API.
        @param health_check_interval: The interval for the health check in seconds.
        """
        self.url = url
        self.token = token
        self.health_check_interval = health_check_interval
        self.last_health_check = datetime.datetime.now()
        self.health_state = "OK"
        self.health_logs = None

        self.l = logging.getLogger("APIDelivery")

    def get_health_state(self) -> Tuple[str, str]:
        """
        Get the API module's last measured health state.
        @return: The function returns a string tuple. The first element is either
            "OK", "WARNING" or "CRITICAL" and indicates the health state. The most severe level is reported. The
            second element is a string-concatenation of log messages or maybe an empty string if everything is okay.
        """
        return self.health_state, self.health_logs

    def do_health_check(self) -> Tuple[str, str]:
        """
        Check if a health check is necessary and potentially perform a health check.
        @return: The function returns a string tuple. The first element is either
            "OK", "WARNING" or "CRITICAL" and indicates the health state. The most severe level is reported. The
            second element is a string-concatenation of log messages or maybe an empty string if everything is okay.
        """
        now = datetime.datetime.now()
        if (now - self.last_health_check).total_seconds() >= self.health_check_interval:
            self.last_health_check = datetime.datetime.now()
            self.l.info("Collecting health check infos from API endpoint.")

            try:
                # Perform a simple GET request to check if the endpoint is reachable
                response = requests.get(
                    self.url,
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10
                )
                if response.status_code == 200 or response.status_code == 204:
                    self.health_state = "OK"
                    self.health_logs = None
                else:
                    self.health_state = "CRITICAL"
                    self.health_logs = f"API endpoint returned status code {response.status_code}"
            except requests.exceptions.RequestException as e:
                self.health_state = "CRITICAL"
                self.health_logs = f"Failed to connect to API endpoint: {str(e)}"

        return self.health_state, self.health_logs

    def send_sms(self, sms: SMS) -> bool:
        """
        Deliver an SMS via the API.

        @param sms: A SMS object to send via the API.
        @return: Returns True if the SMS was successfully sent to the API, False on error.
        """
        self.l.info(f"[{sms.get_id()}] Sending SMS via API to endpoint {self.url}.")

        for i in range(1, 3):
            if i > 1:
                self.l.debug(f"[{sms.get_id()}] Retry sending SMS via API.")

            try:
                # Prepare SMS data
                sms_data = {
                    "sms_id": sms.get_id(),
                    "sender": sms.get_sender(),
                    "recipient": sms.get_recipient(),
                    "text": sms.get_text(),
                    "timestamp": sms.get_timestamp().isoformat(),
                    "flash": sms.is_flash(),
                    "modem_identifier": sms.get_receiving_modem().get_identifier() if sms.get_receiving_modem() else None
                }

                # Send POST request
                response = requests.post(
                    self.url,
                    json=sms_data,
                    headers={"Authorization": f"Bearer {self.token}"},
                    timeout=10
                )

                if response.status_code in (200, 201, 202):
                    self.l.info(f"[{sms.get_id()}] SMS successfully sent via API.")
                    self.health_state = "OK"
                    self.health_logs = None
                    return True
                else:
                    self.l.error(f"[{sms.get_id()}] API returned status code {response.status_code}.")
                    self.health_state = "CRITICAL"
                    self.health_logs = f"API returned status code {response.status_code}"

            except requests.exceptions.RequestException as e:
                self.l.error(f"[{sms.get_id()}] Failed to send SMS via API: {str(e)}")
                self.health_state = "CRITICAL"
                self.health_logs = f"Failed to send SMS via API: {str(e)}"

        return False