import hashlib

class HashUtil:

    def __init__(self):
        pass

    def get_md5(self, fname):
        hash_md5 = hashlib.md5()
        with open(fname, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()


    def get_check_sum(self, checksum_file, content):
        checksum = None
        with open(checksumFile, 'r') as content_file:
            checksum = content_file.read()
        for line in checksum.split("\n"):
            if content in line:
                return line.split(" ")[0].strip()
        return None

    def  validate_check_sum(self, file, name, checksum_file):
        logging.info(
            "Check Checksum for {0} with {1}".format(
                file, checksumFile))
        checksum = self.get_check_sum(checksum_file, "*{0}".format(name))
        logging.info("Calculating Checksum for {0}".format(file))
        targetChecksum = self.get_md5(file)
        logging.info("Got Checksum as {0}".format(targetChecksum))

        if checksum == targetChecksum:
            logging.info("Checksum matched: Expected: {0} <=> Actual: {1}".
                format(checksum, targetChecksum))
            return True
        else:
            logging.error(
                "Checksum didnt not match: Expected: {0} <=> Actual: {1}".
                    format(checksum, targetChecksum))
            return False
