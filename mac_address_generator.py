import random

def get_random_mac():
    """
      Get a random MAC address
    """
    return "50:52:%02x:%02x:%02x:%02x" % (
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
    )
