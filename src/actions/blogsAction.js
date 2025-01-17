import AWS from "aws-sdk";
import {htmlTagCleaner} from "../helpers/HtmlTagCleaner";

export const fetchBlogs = (categories) => {
    return (dispatch) => {
        let lambda = new AWS.Lambda()
        const params = {
            FunctionName: process.env.REACT_APP_FunctionName,
            Payload:JSON.stringify({
                'index': "blogs",
                'categories': categories,
            }),
        };
        lambda.invoke(params, function(err, data) {
            if (err) console.log(err, err.stack); // an error occurred
            else{
                let results = (JSON.parse(data.Payload));
                results = JSON.parse(results)
                results=results.hits.hits
                for(let i=0;i<results.length;i++){
                    results[i]._source.excerpt= htmlTagCleaner(results[i]._source.excerpt)
                }

                dispatch(fetchBlogsSuccess(results))
            }
        });
    }
}
export const fetchBlogsSuccess = (payload) => {
    return {
        type: "FETCH_BLOGS_SUCCESS",
        payload: payload
    }
}
export const fetchAllBlogs = () => {
    return (dispatch) => {
        var params = {
            TableName: "DocumentsTable",
            FilterExpression: "#dtype = :dname",
            ExpressionAttributeNames:{
                "#dtype": "documentType"
            },
            ExpressionAttributeValues: {
                ":dname": "blogs"
            }
        };
        var dynamodb = new AWS.DynamoDB.DocumentClient()
            dynamodb.scan(params, function(err, data) {
                if (err) console.log(err, err.stack); // an error occurred
                else {
                    let allBlogs = data.Items
                    allBlogs.map((item)=>{
                        item.excerpt=htmlTagCleaner(item.excerpt)
                        item.dateModified = new Date(item.dateModified.replace(/-/g, "/")).toLocaleDateString('en-CA');
                    })
                    allBlogs.sort(function(a, b) {
                        return new Date(new Date(b.dateModified)-new Date(a.dateModified))
                    });

                    dispatch(fetchAllBlogsSuccess(allBlogs))
                }

            }
        )
    }

}
export const fetchAllBlogsSuccess = (payload) => {
    return {
        type: "FETCH_ALL_BLOGS_SUCCESS",
        payload: payload
    }
}
