# import flask dependencies
from flask import Flask, request, make_response, jsonify
import json, os
from flask_cors import cross_origin
from SendEmail.sendEmail import EmailSender
from logger import logger
from email_templates import template_reader
from mysqlDB.database import MysqlPython

# initialize the flask app
app = Flask(__name__)

# default route
@app.route('/')
def index():
    return 'Welcome to the Covid-19 Chatbot Webhook'

# function for responses
def results():
    # build a request object
    req = request.get_json(force=True)

    log = logger.Log()
    connect_mysql = MysqlPython()

    responseID          = req.get('responseId')
    queryResult         = req.get("queryResult")
    user_says           = queryResult.get("queryText",'')
    bot_says            = queryResult.get("fulfillmentText",'')
    action              = queryResult.get("action",'')
    reqParamsPresent    = queryResult.get("allRequiredParamsPresent",'')
    queryParameters     = queryResult.get("parameters",'')
    outputContexts      = queryResult.get("outputContexts",'')

    intent              = queryResult.get("intent").get('displayName')

    covid_data          = queryParameters.get("covid_location",'')
    
    if (covid_data!=""):
        #business_name       = covid_data.get("business-name")
        #shortcut            = covid_data.get("shortcut")
        admin_area          = covid_data.get("admin-area",'')      #state
        island              = covid_data.get("island",'')
        city                = covid_data.get("city",'')
        subadmin_area       = covid_data.get("subadmin-area",'')
        zip_code            = covid_data.get("zip-code",'')
        #street_address      = covid_data.get("street-address")
        country             = covid_data.get("country",'')
    else:
        admin_area = island = city = subadmin_area = zip_code = country = ''

    covid_type          = queryParameters.get("covid_type",'')
    covid_date          = queryParameters.get("covid_date",'')
    covid_dur           = queryParameters.get("covid_dur",'')
    covid_date_range    = queryParameters.get("covid_date_range",'')
    
    if (outputContexts!=''):
        contextname         = outputContexts[0].get("name",'')            # "projects/test-agent-mdpfrw/agent/sessions/ea5b6923-b39e-3ec2-6609-e055903a8cd7/contexts/session_var"
        if (contextname!=''):
            splitcontext        = contextname.split("/")
            sessionID           = splitcontext[4]
        else:
            sessionID = ''
        outputContextsParameters = outputContexts[0].get('parameters','')
        if (outputContextsParameters!=''):
            cust_name           = outputContextsParameters.get('cust_name','')
            cust_email          = outputContextsParameters.get('cust_email','')
            cust_contact          = outputContextsParameters.get('cust_contact','')
            cust_city           = outputContextsParameters.get('cust_city','')
        else:
            cust_name = cust_email = cust_contact = cust_city = ''
    else:
        cust_name = cust_email = cust_contact = cust_city = sessionID = ''

    if (cust_name==""):
        cust_userf="Anonymous"
    else:
        cust_userf=cust_name
    
    if (cust_email==""):
        cust_emailf="Anonymous@annony.com"
    else:
        cust_emailf=cust_email
        
    if (cust_contact==""):
        cust_contactf="0000000000"
    else:
        cust_contactf=cust_contact
        
    result = connect_mysql.insert('df_cb_log', SESSION_ID= sessionID, PROJECT_ID=responseID, INTENT_ID=intent, MESSAGE_BY='User', LOG_MESSAGE=user_says, USER_NAME=cust_userf, USER_EMAIL=cust_emailf, USER_CONTACT=cust_contactf, USER_LOCATION=cust_city)
    
    query1 = ''
    query2 = ''
    query2a = " CD_CONFIRMED "

    if (intent=="covid-data") and ((admin_area!="") or (island!="") or (city!="") or (subadmin_area!="") or (zip_code!="") or (country!="") or (covid_date!="") or (covid_type!="") or (covid_date_range!="")):
        # Computation for State
        if ((admin_area!="") or (island!="")):
            if (admin_area!=""):
                textval = "%s%s%s"%("%",admin_area,"%")
            elif (island!=""):
                textval = "%s%s%s"%("%",island,"%")
            else:
                textval = "%s"%("%")
            query1 = "%s and ((detecteddistrict LIKE '%s') or (detectedstate LIKE '%s'))"%(query1,textval,textval)
            query2 = "%s and (CD_PROVINCE LIKE '%s')"%(query2,textval)
        
        # Computation for City
        if ((subadmin_area!="") or (city!="")):
            if (subadmin_area!=""):
                textval = "%s%s%s"%("%",subadmin_area,"%")
            elif (city!=""):
                textval = "%s%s%s"%("%",city,"%")
            else:
                textval = "%s"%("%")
            query1 = "%s and ((detecteddistrict LIKE '%s') or (detectedcity LIKE '%s'))"%(query1,textval,textval)
            query2 = "%s and (CD_CITY LIKE '%s')"%(query2,textval)
            
        # Computation for Country
        if (country!=""):
            if ((country=="India") or (country=="IN")):
                query1 = "%s"%(query1)
                query2 = "%s and (CD_COUNTRY = '%s')"%(query2,country)
            else:
                query1 = "%s"%(query1)
                query2 = "%s and (CD_COUNTRY = '%s')"%(query2,country)
        
        if (covid_date!=""):
            if (covid_dur!=""):
                if (covid_dur=="on"):
                    query1 = "%s and (dateannounced = '%s')"%(query1,covid_date[0:10])
                    query2 = "%s and (CD_DATE = '%s')"%(query2,covid_date[0:10])
                elif (covid_dur=="before"):
                    query1 = "%s and (dateannounced <= '%s')"%(query1,covid_date[0:10])
                    query2 = "%s and (CD_DATE = '%s')"%(query2,covid_date[0:10])
                elif (covid_dur=="after"):
                    query1 = "%s and (dateannounced >= '%s')"%(query1,covid_date[0:10])
                    query2 = "%s and (CD_DATE = '%s')"%(query2,covid_date[0:10])
                else:
                    query1 = "%s and (dateannounced <= '%s')"%(query1,covid_date[0:10])
                    query2 = "%s and (CD_DATE = '%s')"%(query2,covid_date[0:10])
            else:
                query1 = "%s and (dateannounced <= '%s')"%(query1,covid_date[0:10])
                query2 = "%s and (CD_DATE = '%s')"%(query2,covid_date[0:10])


        if (covid_type!=""):
            if (covid_type=="death"):
                query1 = "%s and (currentstatus = 'Deceased')"%(query1)
                query2a = " CD_DEATHS "
            elif (covid_type=="infected"):
                query1 = "%s"%(query1)
                query2a = " CD_CONFIRMED "
            elif (covid_type=="active"):
                query1 = "%s and ((currentstatus = 'Hospitalized') or (currentstatus = 'Migrated'))"%(query1)
                query2a = " CD_ACTIVE "
            elif (covid_type=="recovered"):
                query1 = "%s and (currentstatus = 'Recovered')"%(query1)
                query2a = " CD_RECOVERED "
            else:
                query1 = "%s"%(query1)
                query2a = " CD_CONFIRMED "
        else:
            query2a = " CD_CONFIRMED "

        if (query1==""):
            query1where =""
        else:
            query1where =" WHERE 1 %s"%(query1)
        query1 = "SELECT COUNT(*) FROM inpatientdata %s"%(query1where)
        #print(query1)
        query1result = connect_mysql.select_custom(query1)
        #print(query1result)

        if (query2==""):
            query2where =""
        else:
            query2where =" WHERE 1 %s"%(query2)
        query2 = "SELECT %s FROM coviddata %s"%(query2a,query2where)
        #print(query2)
        query2result = connect_mysql.select_custom(query2)
        #print(query2result)

        if (query1result !=''):
            if (len(query1result) ==1):
                returnText = "%s"%(query1result[0])
            else:
                for i in query1result:
                    returnText = returnText +i
        elif (query2result !=''):
            if (len(query2result) ==1):
                returnText = "%s"%(query2result[0])
            else:
                for i in query2result:
                    returnText = returnText +i
        else:
            returnText = bot_says

        #print(returnText)
        result = connect_mysql.insert('df_cb_log', SESSION_ID= sessionID, PROJECT_ID=responseID, INTENT_ID=intent, MESSAGE_BY='Bot', LOG_MESSAGE=returnText, USER_NAME=cust_userf, USER_EMAIL=cust_emailf, USER_CONTACT=cust_contactf, USER_LOCATION=cust_city)
        return {"fulfillmentText": returnText}
    
    elif ((intent=='user_details') and (cust_name!="") and (cust_contact!="") and (cust_email!="")):
        email_sender=EmailSender()
        template= template_reader.TemplateReader()
        email_message=template.read_course_template('Covid')
        email_sender.send_email_to_student(cust_email,email_message)
        email_file_support = open("email_templates/support_team_Template.html", "r")
        email_message_support = email_file_support.read()
        email_sender.send_email_to_support(cust_name=cust_name,cust_contact=cust_contact,cust_email=cust_email,course_name=course_name,body=email_message_support)
        fulfillmentText="We have sent a welcome email to you with the Covid report of your location."
        result = connect_mysql.insert('df_cb_log', SESSION_ID= sessionID, PROJECT_ID=responseID, INTENT_ID=intent, MESSAGE_BY='Bot', LOG_MESSAGE=fulfillmentText, USER_NAME=cust_userf, USER_EMAIL=cust_emailf, USER_CONTACT=cust_contactf, USER_LOCATION=cust_city)
        #print(fulfillmentText)
        return {"fulfillmentText": fulfillmentText}
    else:
        result = connect_mysql.insert('df_cb_log', SESSION_ID= sessionID, PROJECT_ID=responseID, INTENT_ID=intent, MESSAGE_BY='Bot', LOG_MESSAGE=bot_says, USER_NAME=cust_userf, USER_EMAIL=cust_emailf, USER_CONTACT=cust_contactf, USER_LOCATION=cust_city)
        return {"fulfillmentText": bot_says}


    # return a fulfillment response
    #return {'fulfillmentText': 'This is a response from webhook.'}

# create a route for webhook
@app.route('/webhook', methods=['GET', 'POST'])
@cross_origin()
def webhook():
    # return response
    return make_response(jsonify(results()))

# run the app
if __name__ == '__main__':
   app.run()