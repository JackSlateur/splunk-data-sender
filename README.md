# Splunk Data Sender

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/878ba78c2afd4dd9a37877c0136e49f6)](https://app.codacy.com/manual/andrea.salvatori92/splunk-data-sender?utm_source=github.com&utm_medium=referral&utm_content=Sonic0/splunk-data-sender&utm_campaign=Badge_Grade_Dashboard)

**Splunk Data Sender is a very simple and minimal Python package for sending logged events to an installation of Splunk Enterprise throw REST API**

*This logger requires the destination Splunk Enterprise server to have enabled and configured the [Splunk HTTP Event Collector](http://dev.splunk.com/view/event-collector/SP-CAAAE6M).*

## Installation
Pip:

    pip install splunk-data-sender


Manual:

    python3 setup.py install

## Usage

    from splunk_data_sender import SplunkSender

Then create a SplunkSender instance with your preferred configuration. Now you can use the two methods **send_data()**
and **check_acks()** to, respectively, send logs and check messages acks(Requires useAck enabled in HEC).

Example:

```python
import logging
from splunk_data_sender import SplunkSender


splunk_conf = {
    'endpoint': 'localhost',
    'port': '8000',
    'token': '851A5E58-4EF1-7291-F947-F614A76ACB21',
    'index': 'main',
    'channel': '16c70678-e516-44a9-854d-d139929e6869',  # GUID
    'api_version': '1.0',
    # 'hostname': 'hostname',  # manually set a hostname parameter, defaults to socket.gethostname()
    # 'source': 'source',  # manually set a source, defaults to the log record.pathname
    # 'source_type': '_json',  # manually set a source_type, defaults to 'generic_single_line'
    'allow_overrides': True,  # Whether to look for one of the Splunk built-in parameters(index, host, ecc)
    'verify': False,  # turn SSL verification on or off, defaults to True
    # 'timeout': 60,  # timeout for waiting on a 200 OK from Splunk server, defaults to 60s
    # 'retry_count': 5,  # Number of retry attempts on a failed/erroring connection, defaults to 5
    # 'retry_backoff': 2.0,  # Backoff factor, default options will retry for 1 min, defaults to 2.0
    'enable_debug': True  # turn on debug mode; prints module activity to stdout, defaults to False
}

splunk = SplunkSender(**splunk_conf)

is_alive = splunk.get_health()
logging.info(is_alive)
if not is_alive:
    raise Exception("HEC not alive")

# The first payload is a quote to the italian theme song of Hello!Spank
txt_record = "Hello! Splunk resta con me, Hello! Splunk non te ne andare, Caro Splunk! gioca con me, siamo amici io e te."
json_record = { # this record will be parsed as normal text due to default "sourcetype" conf param
        "source": "spacecraft Discovery 1",
        "host": "HAL9000",
        # "sourcetype": "_json",  # source type without underscore to allow the override of this built-in parameter
        "index": "main",
        "event": {"message": "I am afraid I can't do that Dave.", "severity": "ERROR"},
        "rack": "42",
        "os": "Linux, obvious",
        "arch": "x64"
    }
payloads = [txt_record, json_record]

splunk_res = splunk.send_data(payloads)
logging.info(splunk_res)

ack_id = splunk_res.get('ackId')
splunk_ack_res = splunk.send_acks(ack_id)
logging.info(splunk_ack_res)
```

### Batching support

You may want to enable batching support, to avoid sending a API call to Splunk every time send\_data() is called. \
To enable the feature, use the `max_buf_size` parameter:
```python
from splunk_data_sender import SplunkSender

splunk_conf = {
    'endpoint': 'localhost',
    'port': '8000',
    'token': '851A5E58-4EF1-7291-F947-F614A76ACB21',
    'index': 'main',
    'source_type': '_json',

    # Enable internal buffering, up to 2000 events
    'max_buf_size': 2000,
}

splunk = SplunkSender(**splunk_conf)
```

Then, simply call send\_data() in your loop. API calls will be performed when enough events are gathered. \
Call flush\_buffer() at the end of your code to send remaining events, or if you want to flush the buffer:

```python
for event in generate_event():
	# event may be a dict, a string, or a list of events
	# the event or list of events will be appended to the internal buffer
	# If the buffer holds more than max_buf_size items (2000 in our example),
	# then an API call will be made and the buffer will be reset.
	# If such call is made, send_data returns its result.
	# If no call is made, send_data() returns None
	splunk.send_data(event)

# We finished processing our stuff, we must commit any remaining events to Splunk
splunk.flush_buffer()
```

## Configuration parameters notes
### "source_type"
If this param is sets to "_json" (and "allow_overrides" too), not built-in params will be added inside a **"fields"** key described below.
Refer to the [official Splunk documentation](https://docs.splunk.com/Documentation/Splunk/8.0.5/Data/Listofpretrainedsourcetypes) 
for more information about source types. 

### "allow_overrides"
If this param is set to "True", whether to look for one of the Splunk built-in parameters 
(time, source, host, index) it will override the autocompleted parameters.<br>
For example, a json record with "time"=1486683865.000 will simulates a payload in the past for Splunk.

### Overriding parameters without json
By default, Splunk built-in parameters can only be overwritten from json records.
However, you may need to send non-json records while keeping this ability.
To that purpose, you may use the `event\_formatter` parameter. It takes a function in charge
of formatting events before sending them to Splunk.
Once set, you should call `send_data()` with events formatted as dict.
The library will process the events as if they were json objects, will override the parameters
accordingly, and will then call your function to reformat the resulting event.

A sample code follows:
```python
from splunk_data_sender import SplunkSender


def myEventFormatter(event):
    # Transforms the event in any way you like
    # event is of the same kind of what you sent to send_data()
    # This sample function will return the event as XML, because why not
    import xmltodict
    return xmltodict.unparse({'event': event})

splunk_conf = {
    'endpoint': 'localhost',
    'port': '8000',
    'token': '851A5E58-4EF1-7291-F947-F614A76ACB21',
    'index': 'main',
    'allow_overrides': True,
    'source_type': 'my_source_type',
    'event_formatter': myEventFormatter
}

splunk = SplunkSender(**splunk_conf)

# We can still send non-dict events. The formatter callback must be able to handle whatever
kind of data you use.
txt_record = "Hello! Splunk resta con me, Hello! Splunk non te ne andare, Caro Splunk! gioca con me, siamo amici io e te."

# Built-in parameters will be overridden.
# The resulting dict will be received by the callback function and transformed to XML
json_record = {
    "source": "spacecraft Discovery 1",
    "host": "HAL9000",
    "index": "main",
    "event": {"message": "I am afraid I can't do that Dave.", "severity": "ERROR"},
    "rack": "42",
    "os": "Linux, obvious",
    "arch": "x64"
}
payloads = [txt_record, json_record]
splunk_res = splunk.send_data(payloads)
```

## Notes for JSON source type event 
Refer to the [official Splunk documentation](https://docs.splunk.com/Documentation/Splunk/8.0.5/Data/IFXandHEC) 
for more information about the use of JSON source type.

### Nested JSON inside the "event" property
In some cases, events have nested json which contains the custom fields to be indexed. In this case you have to set "sourcetype" = "_json".

### "fields"
Fields for indexing that do not occur in the event payload itself.<br>
You can use this parameter when you do not want particular fields to be included in the event data, 
but you need additional metadata for indexing and searching.<br>
In the above example, "rack", "os" and "arch" will included inside "fields" key.<br>

Using this method is also typically faster than the nested JSON method.<br>
Be aware that you must send HEC requests containing the fields property to the _/collector/event_ endpoint. Otherwise, they will not be indexed.

## Retry Logic

This library uses the built-in retry logic from urllib3 (a retry counter and a backoff factor). 
Should the defaults not be desireable, you can find more information about how to best configure these
settings in the [urllib3 documentation](https://github.com/kennethreitz/requests/blob/b2289cd2d5d21bd31cf4a818a4e0ff6951b2317a/requests/packages/urllib3/util/retry.py#L104).

## Contributing

Feel free to contribute an issue or pull request:
    
1.  Check for existing issues and PRs
2.  Fork the repo, and clone it locally
3.  Create a new branch for your contribution
4.  Push to your fork and submit a pull request

## License

This project is licensed under the terms of the [MIT license](http://opensource.org/licenses/MIT).
