import io
import json
import logging
import oci

from fdk import response


def handler(ctx, data: io.BytesIO=None):
    if None == ctx.RequestURL():
        return "Function loaded properly but not invoked via an HTTP request."
    signer = oci.auth.signers.get_resource_principals_signer()
    logging.getLogger().info("URI: " + ctx.RequestURL() )
    config = {
        # update with your tenancy's OCID
        "tenancy": "ocid1.fnfunc.oc1.il-jerusalem-1.aaaaaaaa3k2rpmeqaglvehsklbkq5imy6pkv7sa2owjfp5arz4ektn2bnwxa",
        # replace with the region you are using
        "region": "il-jerusalem-1",
        "request_method": ctx.Method()
    }
    # update with your bucket name
    # site bucket
    bucket_site = "bucket-1"
    # data bucket
    bucket_data = "bucket-2"

    file_object_name = ctx.RequestURL()
    if file_object_name.endswith("/"):
        logging.getLogger().info("Adding index.html to reques URL " + file_object_name)
        file_object_name += "index.html"

    # strip off the first character of the URI (i.e. the /)
    file_object_name = file_object_name[1:]

    if config['request_method'] == "GET":
        return read_object(ctx, config, signer, bucket_site, file_object_name)

    if config['request_method'] == "POST":
        return write_object_to_db(ctx, config, signer, bucket_data, data)


def read_object(ctx, config, signer, bucket_name, file_object_name):
    try:
        object_storage = oci.object_storage.ObjectStorageClient(config, signer=signer)
        namespace = object_storage.get_namespace().data

        obj = object_storage.get_object(namespace, bucket_name, file_object_name)
        return response.Response(
            ctx, response_data=obj.data.content,
            headers={"Content-Type": obj.headers['Content-type']}
        )
    except (Exception) as e:
        return response.Response(
            ctx, response_data="500 Server error",
            headers={"Content-Type": "text/plain"}
            )

def write_object_to_db(ctx, config, signer, bucket_name, data):
    try:
        object_storage = oci.object_storage.ObjectStorageClient(config, signer=signer)
        namespace = object_storage.get_namespace().data
        # update with your bucket name
        file_name = "data"

        body = json.loads(data.getvalue())
        user_name = body.get("username")
        email = body.get("email")
        message = body.get("message")

        #object_storage.append_object(namespace, bucket_name, file_name, input_value)
        get_object_response = object_storage.get_object(namespace, bucket_name, file_name)
        contents = get_object_response.data.content.decode()

        # Append the new data to the contents
        contents += '\n'+user_name + ", " + email + ", " + message

        # Write the updated contents back to the file in Oracle Cloud
        object_storage.put_object(namespace, bucket_name, file_name, contents)

    except (Exception, ValueError) as ex:
        logging.getLogger().info('error parsing json payload: ' + str(ex))

        logging.getLogger().info("Inside Python Hello World function")
        return response.Response(
            ctx, response_data=json.dumps(
                {"message": "Succesfuuly added data to file"}),
            headers={"Content-Type": "application/json"}
        )
