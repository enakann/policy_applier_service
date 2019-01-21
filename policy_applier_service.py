from pathlib import Path
import os
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
    def __init__(self,msg):
        self.msg=msg
        self.result_file="result.txt"

    def get_payload(self):
        return self.msg['payload']

    def get_headers(self):
        return self.msg['headers']

    def get_user(self):
        header=self.get_headers()
        return header['username']

    def get_unique_id(self):
        header=self.get_headers()
        return header['unique_id']

    def get_path(self):
        username=self.get_user()
        unique_id=self.get_unique_id()
        return '/home/{}/{}/'.format(username,unique_id)

    def makedir(self):
        result_path=self.get_path()
        path = Path(result_path)
        try:
           path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise e

    def write_result(self):
        self.makedir()
        payload=self.get_payload()
        filename=os.path.join(self.get_path(),self.result_file)
        with open(filename,'w') as file_handler:
            for line in payload:
                file_handler.write(line)
                file_handler.write('\n')


class NotifyUser:
    pass



if __name__ == '__main__':
    msg= {"headers":{
    "unique_id": "99",
    "username": "navi",
    "ticket_num": "123-456",
    "email": "Navaneetha.k.kannan@oracle.com"},
    "payload":"test"}

    obj=JsonToTextFileTransformer(msg)

    obj.write_result()



