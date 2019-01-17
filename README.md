# policy_applier_service

steps:
------
a.Consume message from the PAS-PAP input queue

b.check if request is already processed using request_id in table:Applier_result(class:Validator)

c.if already processed:
     - publish to PAS-PAP ouput queue(request_id:1234 is already procesed)
      return

d.if not already processed:

     1.Transform the message to Applier compatible json (class:ApplierJsonTranformer)
     2.publish the message to PAS-APP queue
     3.APP will start applying the policies
     4.After policy is applied APP publish result to APP-PAS queue
     5.PAS consume message from APP-PAS queue
     6.store it in the db(table:Applier_result)
     7.Write the message into file system based on guid/date/
     8.Construct mail and notify the user
