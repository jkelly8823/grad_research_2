import xml.etree.ElementTree as ET
from langchain.schema import Document

# Load CWE data from XML
def load_cwe_from_xml(file_path: str) -> list:
    tree = ET.parse(file_path)
    root = tree.getroot()
    ns = {"cwe": "http://cwe.mitre.org/cwe-7"}
    docs = []

    for entry in root.findall(".//cwe:Weakness", ns):
        cwe_id = entry.get("ID", "Unknown")
        name = entry.get("Name", "No Name")
        
        # Basic Descriptions
        description = ''.join(entry.find("cwe:Description", ns).itertext()) if entry.find("cwe:Description", ns) else "No description"
        extended_description = ''.join(entry.find("cwe:Extended_Description", ns).itertext()) if entry.find("cwe:Extended_Description", ns) else "No extended description"
        
        # Applicable Platforms
        applicable_platforms = {
            "Languages": [
                {
                    "Name": lang.attrib.get("Name", "Unknown"),
                    "Class": lang.attrib.get("Class", "Unknown"),
                    "Prevalence": lang.attrib.get("Prevalence", "Unknown")
                }
                for lang in entry.findall("cwe:Applicable_Platforms/cwe:Language", ns)
            ],
            "Operating_Systems": [
                {
                    "Name": os.attrib.get("Name", "Unknown"),
                    "Version": os.attrib.get("Version", "Unknown"),
                    "CPE_ID": os.attrib.get("CPE_ID", "Unknown"),
                    "Class": os.attrib.get("Class", "Unknown"),
                    "Prevalence": os.attrib.get("Prevalence", "Unknown")
                }
                for os in entry.findall("cwe:Applicable_Platforms/cwe:Operating_System", ns)
            ],
            "Architectures": [
                {
                    "Name": arch.attrib.get("Name", "Unknown"),
                    "Class": arch.attrib.get("Class", "Unknown"),
                    "Prevalence": arch.attrib.get("Prevalence", "Unknown")
                }
                for arch in entry.findall("cwe:Applicable_Platforms/cwe:Architecture", ns)
            ],
            "Technologies": [
                {
                    "Name": tech.attrib.get("Name", "Unknown"),
                    "Class": tech.attrib.get("Class", "Unknown"),
                    "Prevalence": tech.attrib.get("Prevalence", "Unknown")
                }
                for tech in entry.findall("cwe:Applicable_Platforms/cwe:Technology", ns)
            ]
        }
        
        # Background Details
        background_details = [
            ''.join(detail.itertext())
            for detail in entry.findall("cwe:Background_Details/cwe:Background_Detail", ns)
        ] or ["No background details"]

        # Alternate Terms
        alternate_terms = [
            {
                "Term": term.find("cwe:Term", ns).text if term.find("cwe:Term", ns) else "No Term",
                "Description": ''.join(term.find("cwe:Description", ns).itertext()) if term.find("cwe:Description", ns) else "No Description"
            }
            for term in entry.findall("cwe:Alternate_Terms/cwe:Alternate_Term", ns)
        ]

        # Common Consequences
        common_consequences = [
            {
                "Scope": cons.find("cwe:Scope", ns).text if cons.find("cwe:Scope", ns) else "No Scope",
                "Impact": cons.find("cwe:Impact", ns).text if cons.find("cwe:Impact", ns) else "No Impact",
                "Note": ''.join(cons.find("cwe:Note", ns).itertext()) if cons.find("cwe:Note", ns) else "No Note"
            }
            for cons in entry.findall("cwe:Common_Consequences/cwe:Consequence", ns)
        ]
        
        # Detection Methods
        detection_methods = [
            {
                "Method": dm.find("cwe:Method", ns).text if dm.find("cwe:Method", ns) else "No Method",
                "Description": ''.join(dm.find("cwe:Description", ns).itertext()) if dm.find("cwe:Description", ns) else "No Description",
                "Effectiveness": dm.find("cwe:Effectiveness", ns).text if dm.find("cwe:Effectiveness", ns) else "No Effectiveness"
            }
            for dm in entry.findall("cwe:Detection_Methods/cwe:Detection_Method", ns)
        ]
        
        # Potential Mitigations
        potential_mitigations = [
            {
                "Phase": mit.find("cwe:Phase", ns).text if mit.find("cwe:Phase", ns) else "No Phase",
                "Description": ''.join(mit.find("cwe:Description", ns).itertext()) if mit.find("cwe:Description", ns) else "No Description",
                "Effectiveness": mit.find("cwe:Effectiveness", ns).text if mit.find("cwe:Effectiveness", ns) else "No Effectiveness",
                "Effectiveness_Notes": ''.join(mit.find("cwe:Effectiveness_Notes", ns).itertext()) if mit.find("cwe:Effectiveness_Notes", ns) else "No Notes"
            }
            for mit in entry.findall("cwe:Potential_Mitigations/cwe:Mitigation", ns)
        ]
        
        # Compile all relevant information into a single document
        content = (
            f"CWE-{cwe_id}: {name}\n"
            f"Description: {description}\n"
            f"Extended Description: {extended_description}\n"
            f"Applicable Platforms: {applicable_platforms}\n"
            f"Background Details: {background_details}\n"
            f"Alternate Terms: {alternate_terms}\n"
            f"Common Consequences: {common_consequences}\n"
            f"Detection Methods: {detection_methods}\n"
            f"Potential Mitigations: {potential_mitigations}"
        )
        
        docs.append(Document(page_content=content, metadata={"cwe_id": cwe_id, "name": name, "description": description}))

    return docs

# from dotenv import load_dotenv
# import os
# load_dotenv()
# tmp = load_cwe_from_xml(os.getenv('CWE_SRC'))
# print(tmp)
# print("LEN:", len(tmp))