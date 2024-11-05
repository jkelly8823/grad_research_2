import xml.etree.ElementTree as ET
from langchain.schema import Document

# Load CWE data from XML
def load_cwe_from_xml(file_path: str) -> list:
    tree = ET.parse(file_path)
    root = tree.getroot()
    # Define the namespace
    ns = {"cwe": "http://cwe.mitre.org/cwe-7"}
    docs = []
    # Iterate through each CWE entry
    for entry in root.findall(".//cwe:Weakness", ns):
        cwe_id = entry.get("ID", "Unknown")
        name = entry.get("Name", "No Name")
        
        description = entry.find("cwe:Description", ns).text if entry.find("cwe:Description", ns) is not None else "No description"
        extended_description = entry.find("cwe:Extended_Description", ns).text if entry.find("cwe:Extended_Description", ns) is not None else "No extended description"
        # related_weaknesses = [
        #     rel.attrib.get("CWE_ID", "Unknown") for rel in entry.findall("Related_Weaknesses/Related_Weakness")
        # ] if entry.find("Related_Weaknesses") is not None else ["No related weaknesses"]
        # applicable_platforms = {
        #     "Languages": [
        #         lang.attrib.get("Class", "Not Specified") for lang in entry.findall("Applicable_Platforms/Language")
        #     ],
        #     "Technologies": [
        #         tech.attrib.get("Class", "Not Specified") for tech in entry.findall("Applicable_Platforms/Technology")
        #     ]
        # }
        # background_details = [
        #     rel.text for rel in entry.findall("Background_Details/Background_Detail")
        # ] if entry.find("Background_Details") is not None else ["No background details"]
        # Alternate terms?
        alternate_terms = {
            "Languages": [
                lang.attrib.get("Class", "Not Specified") for lang in entry.findall("cwe:Applicable_Platforms/cwe:Language", ns)
            ],
            "Technologies": [
                tech.attrib.get("Class", "Not Specified") for tech in entry.findall("cwe:Applicable_Platforms/cwe:Technology", ns)
            ]
        }     
        
        # Collect common consequences
        common_consequences = [
            {
                "Scope": cons.find("cwe:Scope", ns).text if cons.find("cwe:Scope", ns) is not None else "No Scope",
                "Impact": cons.find("cwe:Impact", ns).text if cons.find("cwe:Impact", ns) is not None else "No Impact",
                "Note": cons.find("cwe:Note", ns).text if cons.find("cwe:Note", ns) is not None else "No Note"
            } for cons in entry.findall("cwe:Common_Consequences/cwe:Consequence", ns)
        ]
        
        # Collect detection methods
        detection_methods = [
            {
                "Method": dm.find("cwe:Method", ns).text if dm.find("cwe:Method", ns) is not None else "No Method",
                "Description": dm.find("cwe:Description", ns).text if dm.find("cwe:Description", ns) is not None else "No Description",
                "Effectiveness": dm.find("cwe:Effectiveness", ns).text if dm.find("cwe:Effectiveness", ns) is not None else "No Effectiveness"
            } for dm in entry.findall("cwe:Detection_Methods/cwe:Detection_Method", ns)
        ]
        
        # Collect potential mitigations
        potential_mitigations = [
            {
                "Phase": mit.find("cwe:Phase", ns).text if mit.find("cwe:Phase", ns) is not None else "No Phase",
                "Description": mit.find("cwe:Description", ns).text if mit.find("cwe:Description", ns) is not None else "No Description",
                "Effectiveness": mit.find("cwe:Effectiveness", ns).text if mit.find("cwe:Effectiveness", ns) is not None else "No Effectiveness",
                "Effectiveness_Notes": mit.find("cwe:Effectiveness_Notes", ns).text if mit.find("cwe:Effectiveness_Notes", ns) is not None else "No Notes"
            } for mit in entry.findall("cwe:Potential_Mitigations/cwe:Mitigation", ns)
        ]
        
        # Compile all relevant information into a single document
        content = (
            f"CWE-{cwe_id}: {name}\n"
            f"Description: {description}\n"
            f"Extended Description: {extended_description}\n"
            f"Alternate Terms: {alternate_terms}\n"
            # f"Related Weaknesses: {', '.join(related_weaknesses)}\n"
            # f"Applicable Platforms: {applicable_platforms}\n"
            # f"Background Details: {applicable_platforms}\n"
            f"Common Consequences: {common_consequences}\n"
            f"Detection Methods: {detection_methods}\n"
            f"Potential Mitigations: {potential_mitigations}"
        )
        
        docs.append(Document(page_content=content, metadata={"cwe_id": cwe_id, "name": name, "description": description}))
        
        # if len(docs) > 1:
        #     break

    return docs

# from dotenv import load_dotenv
# import os
# load_dotenv()
# tmp = load_cwe_from_xml(os.getenv('CWE_SRC'))
# print(tmp)
# print("LEN:", len(tmp))