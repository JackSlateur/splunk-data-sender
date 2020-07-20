import json
import logging
import socket
import time

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.exceptions import Timeout, ConnectionError, TooManyRedirects


log = logging.getLogger("Splunk-Data-Sender")
logging.basicConfig(format="%(name)s - %(asctime)s - %(levelname)s: - %(message)s")


class SplunkSender:
    """

    A logging handler to send events to a Splunk Enterprise instance
    running the Splunk HTTP Event Collector.
    """

    def __init__(self, host, port, token, index, source="Splunk data sender", hostname=None,
                 allow_overrides=False, sourcetype='generic_single_line', protocol='https', api_url='collector/event',
                 api_version=None, channel=None, channel_in='url', proxies=None, verify=True, timeout=30,
                 retry_count=5, retry_backoff=2.0, enable_debug=False):
        """
        Args:
            protocol (str): The web protocol to use
            host (str): The Splunk host param
            port (int): The port the host is listening on
            token (str): Authentication token
            index (str): Splunk index to write to
            source (str): The Splunk source param
            hostname (str): The Splunk Enterprise hostname
            allow_overrides (bool): Whether to look for _<param> in log data (ex: _index)
            sourcetype (str): The Splunk sourcetype param. Defaults Non-Log files types
                              https://docs.splunk.com/Documentation/Splunk/8.0.5/Data/Listofpretrainedsourcetypes
            api_url (str): The HTTP Event Collector REST API endpoint.
                           https://docs.splunk.com/Documentation/Splunk/8.0.5/Data/HECRESTendpoints
            api_version (str): Protocol version for future scalability. No default version. Refer to the above API docs
            channel (str): GUID. Required if useAck config is enabled in Splunk HEC instance.
            channel_in (str): Where pass channel. "header"("x-splunk-request-channel") or "url".
            proxies (list): The proxies to use for the request
            verify (bool): Whether to perform ssl certificate validation
            timeout (float): The time to wait for a response from Splunk
            retry_count (int): The number of times to retry a failed request
            retry_backoff (float): The requests lib backoff factor
            enable_debug (bool): Whether to print debug console messages
        """

        self.protocol = protocol
        self.host = host
        self.port = port
        self.token = token
        self.index = index
        self.source = source
        self.hostname = hostname or socket.gethostname()
        self.allow_overrides = allow_overrides
        self.sourcetype = sourcetype if sourcetype in ["generic_single_line", "_json"] else "generic_single_line"
        self.api_url = api_url
        self.api_version = api_version or ''
        self.channel = channel
        self.channel_in = channel_in if channel_in in ["url", "header"] else "url"
        self.proxies = proxies
        self.verify = verify  # requests SSL verify. Making unverified HTTPS requests is strongly discouraged
        self.timeout = timeout
        self.session = requests.Session()
        self.retry_count = retry_count
        self.retry_backoff = retry_backoff
        self.debug = enable_debug

        log_level = logging.DEBUG if self.debug else logging.INFO
        log.setLevel(log_level)
        log.debug("Starting in Debug Mode")

        # disable all warnings from urllib3 package
        if not self.verify:
            requests.packages.urllib3.disable_warnings()

        if self.verify and self.protocol == 'http':
            log.error('You should not use SSL Verify and unsecured connection')

        # set proxy to requests session
        if self.proxies:
            self.session.proxies = self.proxies

        if self.api_version and self.api_url == "collector":
            log.error("/collector api does not support versioning")
            raise ValueError("/collector api does not support versioning")

        # https://docs.splunk.com/Documentation/Splunk/8.0.5/Data/FormateventsforHTTPEventCollector
        if self.sourcetype == "_json" and self.api_url in ["collector/raw", f"collector/raw/{self.api_version}"]:
            log.error("cannot send json record as raw data")
            raise ValueError("Json input must be sent either to the /collector or /collector/event endpoints")

        # Set up automatic retry with back-off
        log.debug("Preparing to create a Requests session")
        retry = Retry(total=self.retry_count,
                      backoff_factor=self.retry_backoff,
                      method_whitelist=False,  # Retry for any HTTP verb
                      status_forcelist=[500, 502, 503, 504])
        self.session.mount(f"{self.protocol}://", HTTPAdapter(max_retries=retry))

        log.debug("Class initialize complete")

    def send_data(self, records):
        log.debug("send_data() called")

        if not isinstance(records, list):
            tmp_list = list()
            tmp_list.append(records)
            records = tmp_list.copy()

        payload = ""
        for record in records:
            try:
                formatted_record = self.format_record(record)
                payload = ''.join([payload, formatted_record])
            except Exception as err:
                log.error(f"Exception: {str(err)}")
                raise Exception from err

        splunk_response = self._send_to_splunk(payload=payload)

        return json.loads(splunk_response.text)

    def send_acks(self, acks):
        log.debug("send_acks() called")
        if not isinstance(acks, list):
            tmp_list = list()
            tmp_list.append(acks)
            acks = tmp_list.copy()

        payload = json.dumps({"acks": acks})
        splunk_acks_response = self._send_to_splunk(payload, True)
        return json.loads(splunk_acks_response.text)

    ##################
    # helper methods #
    ##################

    def format_record(self, record):
        log.debug("format_record() called")

        params = {
            'time': self._get_splunk_attr(record, 'time', time.time()),
            'host': self._get_splunk_attr(record, 'host', self.hostname),
            'source': self._get_splunk_attr(record, 'source', self.source),
            'sourcetype': self._get_splunk_attr(record, 'sourcetype', self.sourcetype),
            'index': self._get_splunk_attr(record, 'index', self.index),
            'event': self._get_splunk_attr(record, 'event', record)
        }

        if self.sourcetype == "_json" and isinstance(record, dict):
            params.update({'fields': record})

        log.debug("Record dictionary created")

        formatted_record = json.dumps(params, sort_keys=True)
        log.debug("Record formatting complete")

        return formatted_record

    def _get_splunk_attr(self, obj, attr, default=None):
        log.debug("_get_splunk_attr() called")
        val = default
        if isinstance(obj, dict) and self.allow_overrides:
            val = obj.get(attr, default)
            try:
                del obj[attr]
            except Exception as err:
                log.error(f"Error: {err}, deleting {attr} from {obj}")
        return val

    def _send_to_splunk(self, payload=None, is_acks_call=False):
        log.debug("_send_to_splunk() called")
        if not payload:
            raise ValueError("Please give me a payload to send")
        log.debug("Payload available for sending")

        url, headers = self.dispatch_url_headers(is_acks_call)

        log.debug(f"Destination URL is {url}")
        try:
            log.debug("Sending payload: " + payload)
            splunk_response = self.session.post(
                url,
                data=payload,
                headers=headers,
                verify=self.verify,
                timeout=self.timeout
            )
            self._check_splunk_response(splunk_response)
        except (Timeout, ConnectionError, TooManyRedirects) as err:
            raise err
        else:
            return splunk_response

    def _check_splunk_response(self, splunk_response):
        splunk_res_code = json.loads(splunk_response.text).get('code')
        splunk_api_res_msg = self._dispatch_splunk_res_code(splunk_response.status_code, splunk_res_code)
        msg = f"Splunk response: -code: {splunk_res_code}, -HTTPcode: {splunk_response.status_code}, " \
              f"-message: {splunk_api_res_msg}"
        if msg and splunk_res_code == 0:
            log.info(msg)
        else:
            log.error(msg)

        splunk_response.raise_for_status()  # Throws exception for 4xx/5xx status

    def dispatch_url_headers(self, acks_url=False):
        url = f"{self.protocol}://{self.host}:{self.port}/services"
        if acks_url:
            url = f"{url}/collector/ack"
        else:
            url = f"{url}/{self.api_url}"
            # Add api version
            if self.api_version:
                url = f"{url}/{self.api_version}"

        headers = {'Authorization': f"Splunk {self.token}"}
        # Add Channel
        if self.channel and self.channel_in:
            if self.channel_in == "url":
                url = f"{url}?channel={self.channel}"
                log.debug("Added channel to the url")
            else:  # channel_in == header
                headers = {'Authorization': f"Splunk {self.token}", 'x-splunk-request-channel': self.channel}
                log.debug("Added channel inside the header")

        return url, headers

    @staticmethod
    def _dispatch_splunk_res_code(HTTP_code, splunk_code):
        return {
            200: {0: 'Success'},
            400: {5: 'No data', 6: 'Invalid data format', 7: 'Incorrect index', 10: 'Data channel is missing',
                  11: 'Invalid data channel', 12: 'Event field is required', 13: 'Event field cannot be blank',
                  14: 'ACK is disabled', 15: 'Error in handling indexed fields',
                  16: 'Query string authorization is not enabled'},
            401: {2: 'Token is required', 3: 'Invalid authorization'},
            403: {1: 'Token disabled',
                  4: 'Invalid token'},
            500: {8: 'Internal server error'},
            503: {9: 'Server is busy'},
        }[HTTP_code].get(splunk_code, 'Not a valid Splunk Error')

    @staticmethod
    def dispatch_splunk_health_res_code(HTTP_code):
        return {
            200: 'HEC is available and accepting input',
            400: 'Invalid HEC token',
            503: 'HEC is unhealthy, queues are full',
        }.get(HTTP_code)
