"""BizRadar AI - Document QA Benchmark Dataset."""
from typing import Dict,List
CATEGORY="Document QA"
EXPECTED=True
DIRECT_QA="Direct Question"
ACCORDING_TO="According To"
SECTION_QA="Section Question"
TABLE_FIGURE="Table or Figure"
CROSS_PAGE="Cross Page"
MULTI_DOCUMENT="Multi Document"
CONVERSATIONAL="Conversational"

def make_case(case_id:str,intent:str,difficulty:str,tags:List[str],query:str)->Dict:
    return {"case_id":case_id,"category":CATEGORY,"intent":intent,"difficulty":difficulty,"tags":tags,"query":query,"expected":EXPECTED}

DOCUMENT_QA_CASES=[
make_case("DQA-001",DIRECT_QA,"easy",["qa"],"What does the uploaded report say about revenue?"),
make_case("DQA-002",DIRECT_QA,"easy",["qa"],"What are the key findings in the uploaded document?"),
make_case("DQA-003",DIRECT_QA,"easy",["qa"],"What conclusion does the report reach?"),
make_case("DQA-004",DIRECT_QA,"medium",["qa"],"Does the uploaded report mention cybersecurity risks?"),
make_case("DQA-005",DIRECT_QA,"medium",["qa"],"Which companies are discussed in the report?"),
make_case("DQA-006",DIRECT_QA,"medium",["qa"],"What recommendations are provided in the document?"),
make_case("DQA-007",DIRECT_QA,"hard",["qa"],"What assumptions does the report make?"),
make_case("DQA-008",DIRECT_QA,"hard",["qa"],"What limitations are identified in the uploaded paper?"),
make_case("DQA-009",ACCORDING_TO,"easy",["according-to"],"According to the uploaded report, what is the market outlook?"),
make_case("DQA-010",ACCORDING_TO,"easy",["according-to"],"According to the document, what are the major risks?"),
make_case("DQA-011",ACCORDING_TO,"medium",["according-to"],"Based on the uploaded report, what strategy is recommended?"),
make_case("DQA-012",ACCORDING_TO,"medium",["according-to"],"According to the paper, what problem is being solved?"),
make_case("DQA-013",ACCORDING_TO,"hard",["according-to"],"According to the uploaded document, what future work is suggested?"),
make_case("DQA-014",SECTION_QA,"easy",["section"],"What is discussed in the executive summary?"),
make_case("DQA-015",SECTION_QA,"easy",["section"],"What does the methodology section describe?"),
make_case("DQA-016",SECTION_QA,"medium",["section"],"What is written in the conclusion section?"),
make_case("DQA-017",SECTION_QA,"medium",["section"],"What information appears in the introduction?"),
make_case("DQA-018",SECTION_QA,"hard",["section"],"What is covered in the limitations section?"),
make_case("DQA-019",TABLE_FIGURE,"medium",["table"],"What values are shown in Table 2?"),
make_case("DQA-020",TABLE_FIGURE,"medium",["figure"],"What does Figure 3 illustrate?"),
make_case("DQA-021",TABLE_FIGURE,"hard",["chart"],"Which chart reports the highest market growth?"),
make_case("DQA-022",TABLE_FIGURE,"hard",["graph"],"What trend is shown in the performance graph?"),
make_case("DQA-023",CROSS_PAGE,"hard",["cross-page"],"What trends are consistent throughout the report?"),
make_case("DQA-024",CROSS_PAGE,"hard",["cross-page"],"How do the introduction and conclusion relate?"),
make_case("DQA-025",CROSS_PAGE,"hard",["cross-page"],"Which findings are repeated across multiple sections?"),
make_case("DQA-026",MULTI_DOCUMENT,"medium",["multi-document"],"Which uploaded report predicts higher market growth?"),
make_case("DQA-027",MULTI_DOCUMENT,"hard",["multi-document"],"What common risks are mentioned across both reports?"),
make_case("DQA-028",MULTI_DOCUMENT,"hard",["multi-document"],"How do the conclusions differ between the uploaded documents?"),
make_case("DQA-029",CONVERSATIONAL,"medium",["conversation"],"I uploaded a report. What does it say about pricing?"),
make_case("DQA-030",CONVERSATIONAL,"hard",["conversation","pronoun"],"Can you answer a question about the document I uploaded?"),]
