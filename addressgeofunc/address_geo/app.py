import json

import boto3
import pandas as pd


class AddressGecoder:
    def __init__(self):

        self.json1 = self.GetJsonObj()

        # combining all Irish and County names together
        self.counties = self.PreProcessCountiesList()
        self.address = None

    def main(self, address: str = None):
        """
        Process:
           - prepocess the address
           - Trim the json object so it just contains objects with specific county names
           - Traverse the address list and find if the irish/english town name is present
           - If so return the coordinates from the object
            Params: address: str the string of the address
        """

        try:
            self.address = self.PreProcessAddress(address)
            trimmedJson = self.TrimJsonByCounty()
            coordinates = self.GetTownObjectFromJson(trimmedJson)
            if not coordinates:
                return f"No address found. This is most likely dues to the town not being found in your address. Address is {self.address}"
            else:
                return coordinates

        except Exception as err:
            err1 = f"""There was an error we need to handle this. 
                    Error is {err}"""
            return err1


    def GetJsonObj(self):
        s3 = boto3.resource('s3')

        content_object = s3.Object('accessgeohelper', 'Townlands_-_OSi_National_Placenames_Gazetteer.json')
        file_content = content_object.get()['Body'].read().decode('utf-8')
        json_content = json.loads(file_content)
        return json_content

    def GetTownObjectFromJson(self, trimmedJson):
        """
        Reuturns the coordinates from teh trimeed Json Object
        params: JSON
        """
        for element in self.address:
            for jsonel in trimmedJson:
                if (
                    element == jsonel["properties"]["English_Name"]
                    or element == jsonel["properties"]["Irish_Name"]
                ):
                    return jsonel["geometry"]["coordinates"]
        return False

    def PreProcessCountiesList(self):
        """
        preprocess the counties to match addresses later on
        """
        counties = set.union(
            set(
                [j["properties"]["County"] for j in [i for i in self.json1["features"]]]
            ),
            set(
                [j["properties"]["Contae"] for j in [i for i in self.json1["features"]]]
            ),
        )

        return [county.replace(" ", "").upper() for county in counties]

    def PreProcessAddress(self, address):
        # First split address by comma and make upper case
        self.address = address.split(",")
        self.address = [[i.replace(" ", "").upper() for i in self.address]][0]

        if set(self.counties).intersection(set(self.address)):
            return self.address
        else:
            raise Exception("County not found in address")

    def TrimJsonByCounty(self):
        return [
            j
            for j in [i for i in self.json1["features"]]
            if j["properties"]["County"] in self.address
        ]



###########################
## For testing ##


# pathdf = r"C:\Users\ryderp\Documents\projects\addressGeo\addresses_for_task.csv"
# df = pd.read_csv(pathdf)
# foundGeo = 0
# notFound = 0
# for index, row in df.iterrows():

#     coordinates = geoObj.main(address=row.values[0])
#     print(coordinates)
#     if type(coordinates) == list:
#         foundGeo +=1
#     else:
#         notFound +=1

# print(f'''
#     Coordinates found: {foundGeo}
#     Coordinates not found: {notFound}
# ''')
#################################

def lambda_handler(event, context):
    """Sample pure Lambda function

    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format

        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format

    context: object, required
        Lambda Context runtime methods and attributes

        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict

        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """   
    geoObj = AddressGecoder()
    coordinates = geoObj.main(address=event["queryStringParameters"]["addressstring"])
            
    return {
        "statusCode": 200,
        "body": json.dumps({
            "Message": coordinates,
        }),
    }


            
