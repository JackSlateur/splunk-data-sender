# Splunk Data Sender

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/878ba78c2afd4dd9a37877c0136e49f6)](https://app.codacy.com/manual/andrea.salvatori92/splunk-data-sender?utm_source=github.com&utm_medium=referral&utm_content=Sonic0/splunk-data-sender&utm_campaign=Badge_Grade_Dashboard)

##### Splunk Data Sender is a very simple and minimal Python package for sending logged events to an installation of Splunk Enterprise throw REST API.

*This logger requires the destination Splunk Enterprise server to have enabled and configured the [Splunk HTTP Event Collector](http://dev.splunk.com/view/event-collector/SP-CAAAE6M).*

## Installation

Manual:

    python setup.py install

## Usage

    from splunk_data_sender import SplunkSender

Then create a SplunkSender instance with your preferred configuration. Now you can use the two methods **send_data()**
and **check_acks()** to, respectively, send logs and check messages acks(Requires useAck enabled in HEC).

Example:

```python
    import logging
    from splunk_data_sender import SplunkSender
    
    splunk_conf = SplunkSender(
        host='splunk.example.com',
        port='8088',
        token='851A5E58-4EF1-7291-F947-F614A76ACB21',
        index='main',
        channel='16c70678-e516-44a9-854d-d139929e6869', # GUID
        api_version='0.1',
        #hostname='hostname', # manually set a hostname parameter, defaults to socket.gethostname()
        #source='source', # manually set a source, defaults to the log record.pathname
        #sourcetype='sourcetype', # manually set a sourcetype, defaults to 'text'
        #verify=True, # turn SSL verification on or off, defaults to True
        #timeout=60, # timeout for waiting on a 200 OK from Splunk server, defaults to 60s
        #retry_count=5, # Number of retry attempts on a failed/erroring connection, defaults to 5
        #retry_backoff=2.0,  # Backoff factor, default options will retry for 1 min, defaults to 2.0
        #enable_debug=False, # turn on debug mode; prints module activity to stdout, defaults to False
    )
    
    splunk = SplunkSender(**splunk_conf)
    
    payload = "Hello Splunk!"
    splunk_res = splunk.send_data(payload)
    logging.info(splunk_res)
    
    ack_id = splunk_res.get('ackId')
    splunk_ack_res = splunk.send_acks(ack_id)
    logging.info(splunk_ack_res)
```

## Retry Logic

This library uses the built-in retry logic from urllib3 (a retry
counter and a backoff factor). Should the defaults not be desireable,
you can find more information about how to best configure these
settings in the [urllib3 documentation](https://github.com/kennethreitz/requests/blob/b2289cd2d5d21bd31cf4a818a4e0ff6951b2317a/requests/packages/urllib3/util/retry.py#L104).

## Contributing

Feel free to contribute an issue or pull request:
    
1.  Check for existing issues and PRs
2.  Fork the repo, and clone it locally
3.  Create a new branch for your contribution
4.  Push to your fork and submit a pull request

## License

This project is licensed under the terms of the [MIT license](http://opensource.org/licenses/MIT).
