import AWS from "aws-sdk";

export const fetchClubs = (categories) => {
    return (dispatch) => {
        let lambda = new AWS.Lambda()
        const params = {
            FunctionName: process.env.REACT_APP_FunctionName,
            Payload:JSON.stringify({
                'index': "clubs",
                'categories': categories,
            }),
        };

        lambda.invoke(params, function(err, data) {
            if (err) console.log(err, err.stack); // an error occurred
            else{
                let results = (JSON.parse(data.Payload));
                results = JSON.parse(results)
                dispatch(fetchClubsSuccess(results.hits.hits))
            }
        });
    }
}
export const fetchAllClubs = () => {
    var params = {
        TableName: "DocumentsTable",
        FilterExpression: "#dtype = :dname",
        ExpressionAttributeNames:{
            "#dtype": "documentType"
        },
        ExpressionAttributeValues: {
            ":dname": "clubs"
        }
    };
    return (dispatch) => {
        var dynamodb = new AWS.DynamoDB.DocumentClient()
        dynamodb.scan(params, function(err, data) {
                if (err) console.log(err, err.stack); // an error occurred
                else {
                    let allClubs = data.Items
                    dispatch(fetchAllClubsSuccess(allClubs))
                }
            }
        )
    }
}
export const fetchClubsSuccess = (payload) => {
    return {
        type: "FETCH_CLUBS_SUCCESS",
        payload: payload
    }
}
export const fetchAllClubsSuccess = (payload) => {
    return {
        type: "FETCH_ALL_CLUBS_SUCCESS",
        payload: payload
    }
}
