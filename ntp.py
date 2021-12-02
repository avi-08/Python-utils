from datetime import datetime, timezone
from time import ctime, time, sleep, asctime, strftime

import ntplib


def get_ntp_time():
    ntp_pool = ['time.vmware.com', '0.vmware.pool.ntp.org']# 'ntp1.eng.vmware.com', '10.173.57.2','10.110.75.20', '10.147.7.22']
    try:
        for item in ntp_pool:
            print(item)
            call = ntplib.NTPClient()
            response = call.request(item, version=3)
            times = {"tx":response.tx_time,"recv":response.recv_time,
                     "orig":response.orig_time, "sys":time(),
                     "offset":response.offset, "dest":response.dest_time}
            """print(response.tx_time)
            print(response.recv_time)
            print(response.orig_time)
            print(time())"""
            print(times)
            print(response.tx_time + response.offset)
            print(ctime(response.tx_time))
            print(ctime(response.orig_time))
            t = datetime.fromtimestamp(response.tx_time, timezone.utc)
            print(t.strftime("%Y-%m-%dT%H:%M:%SZ"))
    except ntplib.NTPException as ex:
        print("NTPException: ", ex)

def uk_ntp():
    c = ntplib.NTPClient()
    response = c.request('0.uk.pool.ntp.org', version=3)
    response.offset 
    # UTC timezone used here, for working with different timezones you can use [pytz library][1]
    print (datetime.fromtimestamp(response.tx_time, timezone.utc))


get_ntp_time()
