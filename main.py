from os import environ
from dotenv import load_dotenv
import psycopg2
import pymongo
# from face import face
# from finger import finger
from requests import Response, get

load_dotenv()

# client = pymongo.MongoClient(environ.get('MONGO_URI'))
# mongo_db = client.procard
mongo_db = {}
aws_file_host = environ.get('AWS_FILE_HOST')
conn = psycopg2.connect(f"""dbname={environ.get('PSQL_DATABASE')} 
                        user={environ.get('PSQL_USERNAME')}
                        host={environ.get('PSQL_HOSTNAME')} 
                        password={environ.get('PSQL_PASSWORD')} 
                        port={environ.get('PSQL_PORT')}""")

registration_field_list = ['id', 'enrolment_no', 'account_terminal_id',
                            'company_id', 'use_case_id', 'nni', 'id_card_number',
                            'last_name', 'first_name', 'spouse_name', 'full_name',
                            'gender', 'datas', 'status', 'score', 'note', 'updated_by',
                            'deleted_by', 'created_at', 'updated_at', 'deleted_at', 
                            'inprogress', 'transmitted']
citizen_field_list = ['id', 'nni', 'is_temp_nni', 'id_card_number', 'last_name', 
                      'first_name', 'spouse_name','gender', 'birth_date', 'birth_town', 
                      'birth_country', 'nationality', 'father_last_name', 'father_first_name', 
                      'father_spouse_name', 'father_birth_date', 'father_birth_town',
                      'father_nni', 'mother_last_name', 'mother_first_name', 
                      'mother_spouse_name', 'mother_birth_date', 'mother_birth_town', 
                      'mother_nni', 'other', 'created_at', 'updated_at']


def pg_get_all_registration():
    registrations = []
    fields_str = ', '.join(registration_field_list)

    with conn.cursor() as cur:
        cur.execute("SELECT %s FROM registrations" % (fields_str))
        
        registrations = [parse_pg_data(item, registration_field_list) \
                            for item in cur.fetchall()]
    
    return registrations


def pg_get_all_citizen():
    citizens = []
    fields_str = ', '.join(citizen_field_list)

    with conn.cursor() as cur:
        cur.execute("SELECT %s from citizens" % (fields_str))
        citizens = cur.fetchall()

        citizens = [parse_pg_data(item, citizen_field_list) \
                    for item in cur.fetchall()]
    
    return citizens


def pg_set_registration_in_progress(id, value):
    with conn.cursor() as cur:
        cur.execute("""UPDATE registrations 
                    SET inprogress=%s 
                    WHERE id=%s""", (value, id))


def parse_pg_data(data, field_list):
    data_dict = {}
    
    for index in range(0, len(data) - 1):
        data_dict[field_list[index]] = \
            data[index] if data[index] is not None else None
        
    return data_dict


def is_registration_match_citizen_info(registration, citizen):
    is_match = True
    field_list = ['id_card_number', 'last_name', 'first_name',
                          'spouse_name', 'full_name', 'gender']
    
    for field in field_list:
        if registration[field] != citizen[field]: is_match = False

    return is_match


def mongo_get_all_enrolment():
    return mongo_db.enrolments.find()


def create_file(path, content):
    with open(path, 'wb') as file:
        file.write(content)

    return path

def match_face(source_img_url, target_img_url, 
               image_path_1, image_path_2) -> bool:
    
    file_1_binary: Response = get(
        f'{aws_file_host}{source_img_url}'
    ).content
    file_2_binary: Response = get(
        f'{aws_file_host}{target_img_url}'
    ).content

    with open(image_path_1, 'wb') as file: file.write(file_1_binary)
    with open(image_path_2, 'wb') as file: file.write(file_2_binary)

    # return face.face(image_path_1, image_path_2)


def init():
    try:
        with conn:
            citizen_list = pg_get_all_citizen()
            registration_list = pg_get_all_registration()

            for registration_item in registration_list:
                is_matched = False
                has_citizen = False

                pg_set_registration_in_progress(registration_item['id'], "1")

                for citizen_item in citizen_list:
                    if registration_item['nni'] is None or \
                        (registration_item['nni'] != citizen_item['nni']):
                        
                        has_citizen = is_registration_match_citizen_info(
                            registration_item, citizen_item)
                        
                        if has_citizen is True:
                            is_matched = match_face(
                                source_img_url=registration_item['datas']['biometric_datas']\
                                    ['biometric_facial_image'],
                                target_img_url=citizen_item['biometric_facials']['facial_image'],
                                image_path_1='./face/data/image_1.jpg',
                                image_path_2='./face/data/image_2.jpg'
                            )
                            # match finger

                    else:
                        has_citizen = True

                        is_matched = match_face(
                            source_img_url=registration_item['datas']['biometric_datas']\
                                ['biometric_facial_image'],
                            target_img_url=citizen_item['biometric_facials']['facial_image'],
                            image_path_1='./face/data/image_1.jpg',
                            image_path_2='./face/data/image_2.jpg'
                        )

                        # match and finger
                
                pg_set_registration_in_progress(registration_item['id'], "0")

                if is_matched is False:
                    if has_citizen is True:
                        print("set registration_item status to award")
                        
                        # set registration_item status to award
                    else:
                        print("set registration_item status to coated")
                        # create citizens
                        # set registration_item status to coated

                else:
                    print("set registration_item status to exist")
                    # set registration_item status to exist

        conn.close()
    except Exception as e:
        conn.close()
        print(e)


init()