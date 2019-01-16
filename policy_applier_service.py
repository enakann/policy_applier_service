class Validator:
    """Verify is the message is already processed or not """
    def __init__(self,header,msg):
        self.header=header
        self.msg=msg
        self.tablename="applier_result"

    def get_header_payload(self):
        return self.msg['headers'], self.msg["payload"]

    def get_header(self):
        return self.msg['headers']

    def get_msg_from_datastore(self, query_str,corrid):
        """ method check if message for the passed corrid in the service datastore table"""

        try:
            with DataStore (self.db) as dbobj:
                return dbobj.select_data (query_str, (corrid,))
        except Exception as e:
            logger.exception (e)
            raise e

    def process(self):
        header = self.get_header()
        query_str = "select * from {} where correlation_id=:1 ".format (self.tablename)
        try:
           ret = self.get_msg_from_datastore (query_str,header["correlation_id"])
        except Exception as e:
            logger.exception(e)
            raise e
        if not ret:
            return True
        return False



class BuilderToApplierJsonTranformer:
    def __init__(self,new_policy):
        self.new_policy=new_policy
    def trasform(self):
        """Transform Builder json to Appler Json data"""

class JsonToTextFileTransformer:
    pass

class NotifyUser:
    pass






