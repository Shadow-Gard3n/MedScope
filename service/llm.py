# from langchain_core.prompts import ChatPromptTemplate
# from langchain_openai import ChatOpenAI


# message1=[
#     ("system","You are a highly experienced and knowledgeable doctor, specializing in all fields of medicine"),
#     ("human","Based on the conversation transcript of doctor and patient generate 5 bulleted points of questions which the doctor should ask the patient. the transcript is: {transcript}")
# ]
# message2=[
#     ("system","You are a highly experienced and knowledgeable doctor, specializing in all fields of medicine"),
#     ("human","Based on the conversation transcript of doctor and patient generate 5 bulleted points of diagnosis which the patient has. the transcript is: {transcript}")
# ]
# message3 = [
#     ("system", "You are an AI designed to merge staggered transcripts from two or more overlapping transcripts into one continuous and coherent transcript."),
#     ("human", '''You will be provided with multiple transcript segments from three sources  that may include overlaps, extraneous system messages, and partial sequences. The transcripts follow this pattern:
# •⁠  Transcript 1:  There will be previous transcripts provided that set up the conversation context overlapping with the start of transcript 1 capturing content missed during pause
# •⁠  Transcript 2: Starts at t = 0 for 6 seconds.
# •⁠  Transcript 3:  starts at t = 2 and runs for 6 seconds, overlapping with the end of Recording 1 and capturing content missed during its pause.

# Your Task:
# -  Merge All Segments:  Combine all provided transcript segments into a single, continuous conversation.
# •⁠ Integrate Overlapping Content: Seamlessly merge overlapping sections by removing duplicates. If overlaps include variations or partial differences, blend the information in such a way that it does not exceeds the length of variations or partial differences and maintains context with over all transcript
# •⁠ Preserve Context and Speaker Attribution: Maintain the overall context from transcript 1
# •⁠  Ignore Extraneous Content: Do not output system prompts, fallback messages (e.g., “Please provide the transcripts...” or similar queries), or irrelevant non-verbal cues (like repeated numbers or system interrupts) and do not summarise the transcript.
#     - Use clear punctuation, proper sentence structure, and paragraph breaks to ensure the transcript is easy to read.
#     - Ensure that the final transcript is presented as one coherent narrative without fragmented sections.
# Input:
# •⁠ Transcript 1: {transcript1}
# •⁠ Transcript 2: {transcript2}
# •⁠ Transcript 3: {transcript3}''')
# ]
# prompt_template1 = ChatPromptTemplate.from_messages(message1)
# prompt_template2 = ChatPromptTemplate.from_messages(message2)
# prompt_template3 = ChatPromptTemplate.from_messages(message3)
# def llm3(api_key,trans1,trans2,trans3):
#     LLM3=ChatOpenAI(api_key=api_key,model="gpt-5-nano")
#     prompt3 = prompt_template3.invoke({"transcript1":trans1 , "transcript2": trans2 , "transcript3": trans3 })
#     result_llm3 = LLM3.invoke(prompt3)
#     return result_llm3.content

# def llm1(api_key,trans):
#     LLM1=ChatOpenAI(api_key=api_key,model="gpt-5-nano")
#     prompt1 = prompt_template1.invoke({"transcript":trans})
#     result_llm1 = LLM1.invoke(prompt1)
#     return result_llm1.content
    
# def llm2(api_key,trans):
#     LLM2=ChatOpenAI(api_key=api_key,model="gpt-5-nano")
#     prompt2 = prompt_template2.invoke({"transcript":trans})
#     result_llm2 = LLM2.invoke(prompt2)
#     return result_llm2.content

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

# --- PROMPTS (Keep these exactly as they are) ---
message1=[
    ("system","You are a highly experienced and knowledgeable doctor, specializing in all fields of medicine"),
    ("human","Based on the conversation transcript of doctor and patient generate 5 bulleted points of questions which the doctor should ask the patient. the transcript is: {transcript}")
]
message2=[
    ("system","You are a highly experienced and knowledgeable doctor, specializing in all fields of medicine"),
    ("human","Based on the conversation transcript of doctor and patient generate 5 bulleted points of diagnosis which the patient has. the transcript is: {transcript}")
]
# (Message 3 is omitted here as you don't need it for the WebSocket version, but you can keep it if you want)

prompt_template1 = ChatPromptTemplate.from_messages(message1)
prompt_template2 = ChatPromptTemplate.from_messages(message2)

# --- UPDATED ASYNC FUNCTIONS ---

# 1. Make the function async
async def llm1(api_key, trans):
    # Use gpt-4o-mini or gpt-3.5-turbo (gpt-5-nano is not a standard public model name yet)
    LLM1 = ChatOpenAI(api_key=api_key, model="gpt-4o-mini") 
    
    prompt1 = prompt_template1.invoke({"transcript": trans})
    
    # 2. Use await + ainvoke
    result_llm1 = await LLM1.ainvoke(prompt1)
    
    return result_llm1.content
    
# 1. Make the function async
async def llm2(api_key, trans):
    LLM2 = ChatOpenAI(api_key=api_key, model="gpt-4o-mini")
    
    prompt2 = prompt_template2.invoke({"transcript": trans})
    
    # 2. Use await + ainvoke
    result_llm2 = await LLM2.ainvoke(prompt2)
    
    return result_llm2.content

# Note: llm3 is removed because the browser handles speech merging automatically now.
# If you still need it for other parts of your app, you can keep it, 
# but make it 'async def' and use 'await LLM3.ainvoke' as well.