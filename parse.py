import os

import regex as re
import nltk
from flask import Flask, request, jsonify
from flask_cors import CORS
from dateutil.parser import parse
#from tika import parser
import textract
from pyresparser import ResumeParser
import entities as en
from urlextract import URLExtract
#from convertPDFToText import convertPDFToText

import spacy
trained_NER = spacy.load('/home/riteshjain/Documents/Entity-Recognition-In-Resumes-SpaCy-master/nlp_train')


app = Flask(__name__)
CORS(app)

extractor = URLExtract()

UPLOAD_FOLDER = "/home/riteshjain/Desktop/cv_parsing/"

def is_date(string, fuzzy=False):
    try: 
        parse(string, fuzzy=fuzzy)
        return True

    except ValueError:
        return False

def extractDOB(text_):
    possible_kw = ["date of birth", "dob ", "birthdate", "birth date", "birth-date"]

    dob = []
    for line in text_.split("\n"):
        data = text_.split('\n') 
        data = [x.lower() for x in data] 
        data = list(filter(None, data)) 
        in_ = [kw for kw in possible_kw if kw in line.lower()]
        if len(in_) > 0:
            try:
                date = data[data.index(in_[0]) + 1]
                dob.append(date)
            except:
                print('None')
                date = line.lower().replace(in_[0],"").strip()
                dob.append(date)
        else:
            pass
    if len(dob) > 0 :
        return dob[0]
    else:
        return None

def marital(text_):
    value = ['marital status']
    status = ['single', 'married']

    stat = []
    for line in text_.split("\n"):
        data = text_.split('\n') 
        data = [x.lower() for x in data] 
        data = list(filter(None, data)) 
        in_ = [val for val in value if val in line.lower()]
        if len(in_) > 0:
            try:
                a = data[data.index(in_[0]) + 1]
            except:
                print('None')
                a = line.lower().replace(in_[0],"").strip()
            if a in status:
                stat.append(a)
        else:
            pass
    if len(stat) > 0 :
        return stat[0]
    else:
        return None

def nation(text_):
    value = ['nationality']

    nation = []
    for line in text_.split("\n"):
        data = text_.split('\n') 
        data = [x.lower() for x in data] 
        data = list(filter(None, data))
        in_ = [val for val in value if val in line.lower()]
        if len(in_) > 0:
            try:
                a = data[data.index(in_[0]) + 1]
            except:
                print('None')
                a = line.lower().replace(in_[0],"").strip()
            nation.append(a)
        else:
            pass
    if len(nation) > 0 :
        return nation[0]
    else:
        return None

def gen(text_):
    value = ['gender']
    status = ['Male', 'Female', 'Transgender']

    gend = []
    for line in text_.split("\n"):
        data = text_.split('\n') 
        data = [x.lower() for x in data] 
        data = list(filter(None, data))
        in_ = [val for val in value if val in line.lower()]
        if len(in_) > 0:
            try:
                a = data[data.index(in_[0]) + 1]
            except:
                print(None)
                a = line.lower().replace(in_[0],"").strip()
            gend.append(a)
        else:
            pass
    if len(gend) > 0 :
        return gend[0]
    else:
        return None

def link_remove(t):
    links = extractor.find_urls(t)
    if len(links) > 0:
        for l in links:
            t = t.replace(l, '')
            return t
    else:
        return t

def remove_common_words(t):
    words = ['resume', 'curriculum', 'vitae', 'name']

    for w in words:
        if t.lower().find(w) >= 0:
            t = t.replace(t[t.lower().find(w):(t.lower().find(w)+len(w))],"")
    return t

def getExpEdu(text):
    text = remove_common_words(text)
    doc_to_test=trained_NER(text)
    
    entities={}
    for ent in doc_to_test.ents:
        entities[ent.label_]=[]
    for ent in doc_to_test.ents:
        entities[ent.label_].append(ent.text)

    ed = []
    ex = []
    for i in range(3):
        exp = {
            "currentIndicator":None,
            "duration": {"start":None, "end":None}
            }
        edu = {"currentIndicator":None}

        try:
            if not entities['Companies worked at'][i].strip().isdigit():
                exp["organization"]=  link_remove(entities['Companies worked at'][i]).strip()
            else:
                exp["organization"] = None
        except:
            exp["organization"] = None

        try:
            if not entities['Designation'][i].strip().isdigit():
                exp["profile"]=link_remove(entities['Designation'][i]).strip()
            else:
                exp["profile"] = None
        except:
            exp["profile"] = None

        try:
            if not entities['College Name'][i].strip().isdigit():
                edu["university"]= link_remove(entities['College Name'][i]).strip()
            else:
                edu["university"] = None
        except:
            edu["university"] = None

        try:
            if not entities['Degree'][i].strip().isdigit():
                edu["educationDegree"]= link_remove(entities['Degree'][i]).strip()
            else:
                edu["educationDegree"] = None    
        except:
            edu["educationDegree"] = None

        try:
            if entities['Graduation Year'][i].strip().isdigit():
                edu["year"]= entities['Graduation Year'][i].strip()
                edu['year'] = link_remove(edu["year"])
            else:
                edu["year"] = None
        except:
            edu["year"] = None

        ed.append(edu)
        ex.append(exp)

    return ex, ed

@app.route("/")
def home():
    return "running"

@app.route("/parsecv",methods=["POST"])
def parseCV2():
    try:
        if request.method == 'POST':
            f = request.files['file']  
            f.save(UPLOAD_FOLDER+f.filename)

            data = ResumeParser(UPLOAD_FOLDER+f.filename).get_extracted_data()  
            text = textract.process(UPLOAD_FOLDER+f.filename)
            text = text.decode("utf-8")
        
            data['birth_date'] = extractDOB(text)
            data['marital_status'] = marital(text)
            data['nationality'] = nation(text)
            data['gender'] = gen(text)
            
            text = text.encode("utf-8").decode("ascii","ignore").replace("\n"," ").strip()

            exp, edu = getExpEdu(text)
            stopwords = set(nltk.corpus.stopwords.words('english'))
            stopwords.update(['resume', 'curriculum', 'vitae'])

            filters=':'
            translate_dict = dict((c, " ") for c in filters)
            translate_map = str.maketrans(translate_dict)
            text = text.translate(translate_map)

            text = ' '.join([w for w in text.split() if w not in stopwords])  

            ent = en.extract_entity_sections_grad(text)

            if 'certifications' in ent.keys():
                a = ent['certifications']
                cert = " ".join(a)
                data['certifications'] = cert
            else:
                data['certifications'] = None

            pro = ['project', 'projects', 'project profile']
            if len([p for p in pro if p in ent.keys()]) > 0:
                a = ent[[p for p in pro if p in ent.keys()][0]]
                proj = " ".join(a)
                data['projects'] = proj
            else:
                data['projects'] = None

            if 'hobbies' in ent.keys():
                a = ent['hobbies']
                hob = " ".join(a)
                data['hobbies'] = hob
            else:
                data['hobbies'] = None

            if 'summary' in ent.keys():
                a = ent['summary']
                res = " ".join(a)
                data['summary'] = res
            else:
                data['summary'] = None

            if 'objective' in ent.keys():
                b = ent['objective']
                rest = " ".join(b)
                data['objective'] = rest
            else:
                data['objective'] = None

            # data["experience"] = [{
            #             "organization":None,
            #             "profile": None,
            #             "currentIndicator":None,
            #             "duration": {"start":None, "end":None}
            #             }]


            
            links = extractor.find_urls(text)
            if (len(links) > 0):     
                for link in links:
                    if "github" in link:
                        data['github'] = link
                    else:
                        data['github'] = None
            
                for link in links:
                    if "linkedin" in link:
                        data['linkedin'] = link
                    else:
                        data['linkedin'] = None

                for link in links:
                    if "skype" in link:
                        data['skype'] = link
                    else:
                        data['skype'] = None
            else:
                data['linkedin'] = None
                data['github'] = None
                data['skype'] = None

            url = ['linkedin', 'github', 'skype']

            for ur in url:
                for i in range(len(links)):
                    if ur in links[i]:
                        links[i] = links[i].replace(links[i], "")
            links = list(filter(None, links))
            links = list(set(links))
            data['webpage'] = links
                    
            data["skills"] = [i.upper() for i in data["skills"]]
            if ((isinstance(data["education"], list)) and (len(data["education"]) > 0)):
                data["qualification"] = []
                for ed in data["education"]:
                    if isinstance(ed, tuple):
                        data["qualification"].append({"educationDegree":ed[0], "year":ed[1] , "university":None, "currentIndicator":None})
                    else:
                        data["qualification"].append({"educationDegree":ed, "year":None, "university":None, "currentIndicator":None})
            else:
                data['qualification'] = None

            print(data['qualification'])
            if edu[0]['educationDegree'] == None:
                data["education"] = data["qualification"]
            else:
                data["education"] = edu
            data["experience"] = exp
            # data["education"] = edu
            data["success"] = True

            data['first_name'] = None
            data['middle_name'] = None
            data['last_name'] = None

            if len(data['name'].split()) > 0:
                data['first_name'] = data['name'].split()[0]
                if len(data['name'].split()) > 2:
                    data['middle_name'] = data['name'].split()[1]
                    data['last_name'] = data['name'].split()[-1]
                elif len(data['name'].split()) == 2:
                    data['last_name'] = data['name'].split()[-1]
                else:
                    pass            

            output_data = { 
                "status": True,
                "message" : "Cv Parsed Successfully",
                "inputFile": f.filename,
                "data" :{
                            "objective": data['objective'],
                            "summary": data['summary'],
                            "personalInfo": {
                                                "fullName": data["name"],
                                                "firstName": data["first_name"],
                                                "middleName": data['middle_name'],
                                                "lastName": data["last_name"],
                                                "maritialStatus" : data['marital_status'],
                                                "dateOfBirth" : data['birth_date'],
                                                "nationality" : data['nationality'],
                                                "gender" : data['gender'],
                                                "language": None,
                                                "address": None,
                                                "hobbies": data['hobbies'],
                                                "passportNumber": None
                                            },
                            "contactInfo":  {                   
                                                "email": data["email"],
                                                "telephone": data["mobile_number"],
                                                "currentLocation": None,
                                                "webpage": data['webpage'],
                                            },
                            "socials":      { 
                                                "githubURL": data['github'],
                                                "linkedinURL": data['linkedin'],
                                                "skype": data['skype']
                                            },
                            "education": data["education"],
                            "experience": data["experience"],
                            "skills": data["skills"],
                            "projects": {
                                "name": data['projects'],
                                "detail": None
                                },
                            "certification": {
                                "subject": data['certifications'],
                                "provider": None,
                                },
                            "publications":{
                                "title": None,
                                "publisher": None,
                                "monthYear": None
                                },
                            "achievements": {
                                "name": None,
                                "detail": None
                                }
                            }
                    }  

    # output_data = { "objective": data['objective'],
    #                 "summary": data['summary'],
    #                 "personal_info": {
    #                                     "name": data["name"],
    #                                     "email": data["email"],
    #                                     "mobileNumber": data["mobile_number"],
    #                                     "githubURL": data['github'],
    #                                     "linkedinURL": data['linkedin'],
    #                                     "firstName": data["first_name"],
    #                                     "middleName": data['middle_name'],
    #                                     "lastName": data["last_name"],
    #                                     "maritialStatus" : data['marital_status'],
    #                                     "dateOfBirth" : data['birth_date'],
    #                                     "nationality" : data['nationality'],
    #                                     "gender" : data['gender'], 
    #                                     "hobbies": data['hobbies'],
    #                                     "projects": data['projects'],
    #                                     "certifications":data['certifications'],

    #                                 },
    #                 "education": data["qualification"],
    #                 "experience": data["experience"],
    #                 "skills": data["skills"],
    #                 "success": True
    #                 }       
    #os.remove(UPLOAD_FOLDER+f.filename)
            return jsonify(output_data)
        else:
            return jsonify({"success":False}), 400
    except Exception as e:
        return jsonify({"success":False}), 400          

@app.route("/parse",methods=["POST"])
def parseCV():
    try:
        #print (request.get_json()['file'])
        file_path = request.get_json()['file']
        print(file_path)
        if os.path.exists(file_path):
            #print("file exists")
            data = ResumeParser(file_path).get_extracted_data()
            #print ("result",data)
            data["success"] = True
            return jsonify(data)
        else:
            return jsonify({"success":False})
    except Exception as e:
        return jsonify({"success":False})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7000, debug=True)
