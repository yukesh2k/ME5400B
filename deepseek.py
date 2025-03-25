# from groq import Groq

API_URL = "https://api.groq.com/openai/v1/chat/completions"
API_KEY = "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"

MODEL = "deepseek-r1-distill-llama-70b"

# client = Groq(api_key="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")
# completion = client.chat.completions.create(
#     model="deepseek-r1-distill-llama-70b",
#     messages=[
#         {
#             "role": "user",
#             "content": "What is the capital of india? be concise",
#         }
#     ],
#     temperature=0.6,
#     max_completion_tokens=4096,
#     top_p=0.95,
#     stream=True,
#     stop=None,
# )

# for chunk in completion:
#     print(chunk.choices[0].delta.content or "", end="")

import json
import requests
import time
import re
import os
from tqdm import tqdm

# Define the System Prompt
SYSTEM_PROMPT = """You are an AI assistant that converts natural language robotic commands into structured JSON format.

## Environment Details:
- There are only three objects:  
  1. The robotic arm (location: "ARM_LOCATION")  
  2. A cup (location: "CUP_LOCATION")  
  3. A table (location: "TABLE_LOCATION")  

## Coordinate Axis System:
- The following coordinate axes are defined relative to the end-effector's **initial pose and orientation**:
  - **x-axis**: Forward and backward along the arm's direction of movement (in front and behind the end effector).
  - **y-axis**: Left and right (perpendicular to the x-axis, on the horizontal plane).
  - **z-axis**: Up and down (vertical direction, perpendicular to both x and y axes).
- These axes are **fixed** globally for all commands and constraints, meaning that the robot interprets any relative motion in terms of these axes, regardless of the arm's current position.

## Action Constraints:
- The robotic arm can only perform **three actions**:  
  - "move" (move the end effector)  
  - "release" (open the gripper)  
  - "close" (close the gripper)  

## Understanding Relative Positioning:
- The robotic arm may need to execute commands with respect to relative positions such as "behind the table" or "in front of the arm". For such commands, consider the current object’s position and offset. For example, if the command is "move the cup behind the table," the system will interpret this as:
  - **location**: "TABLE_LOCATION"
  - **offset**: [some displacement in x, y, z based on the object's position relative to the table]

- If the command is vague, such as "move the cup near the table" or "move the arm in front of the table," the system should infer reasonable default values for the relative positions. This can include moving the cup or arm just behind or in front of the table or arm, using a small default offset.

## Constraints:
Commands can impose movement constraints on the **end effector**. The end effector can be referred to directly or indirectly in commands.  

- **Positional Constraint** (modeled as a **cylinder**):  
  - `"position": ["FLOOR_LOCATION", radius]`  
  - If the radius exceeds 1.0, split into multiple constraints.  

- **Orientational Constraint** (limits rotation around a specific axis):  
  - `"orientation": ["axis", max_degrees]`  

- **Kinematic Constraint** (limits velocity along a specific axis):  
  - `"kinematics": ["axis", max_velocity]`  

- If multiple constraints are imposed, they should be placed in a **single list** and applied to the appropriate actions within the command. Do not create separate tasks for each constraint.  

## Output Formatting:
- **Return ONLY a valid JSON array**—no explanations, extra text, or formatting.  
- If a command requires multiple base actions, **break it down into sequential steps** within the JSON array.  
- The `"location"` field should only contain `"ARM_LOCATION"`, `"CUP_LOCATION"`, or `"TABLE_LOCATION"`, along with offsets in `[x, y, z]` format.  
- If constraints exist, they should be included in each step's `"constraint"` field as a **list**.  

### Example Output:
#### **Command:** "Move the cup behind the table with a positional constraint of 0.5 meters and an orientation constraint of 10 degrees rotation around the y-axis."
#### **Correct JSON Output:**
```json
[
    {
        "action": "move",
        "object": "cup",
        "location": "TABLE_LOCATION",
        "offset": [0.0, -0.2, 0.0],
        "constraint": [
            {
                "type": "positional",
                "position": ["FLOOR_LOCATION", 0.5]
            },
            {
                "type": "orientation",
                "orientation": ["y", 10]
            }
        ]
    },
    {
        "action": "close",
        "object": "cup",
        "location": "TABLE_LOCATION",
        "offset": [0.0, -0.2, 0.0]
    }
]
"""

# Function to call DeepSeek API
def query_deepseek(prompt):
    headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    response_json = response.json()
    
    if "choices" in response_json:
        return response_json["choices"][0]["message"]["content"].strip()
    else:
        print("Error:", response_json)
        return None

def loading_bar(duration):
    # Create a tqdm progress bar with the specified duration
    for _ in tqdm(range(duration), desc="Loading", ncols=100, ascii=True):
        time.sleep(1)

def extract_command_after_keyword(text):
    # Regular expression to find the command inside the quotation marks after **Command:**
    match = re.search(r'\*\*Command:\*\* "(.*?)"', text)
    
    if match:
        return match.group(1).strip().replace("\"", "")  # Return the captured part inside the quotes
    return None

def extract_json_after_json_keyword(text):
    # Regular expression to match everything after the word "json" and remove ''' from the start and end
    match = re.search(r'json(.*)', text, re.DOTALL)
    
    if match:
        # Extract the text after "json" and strip the leading/trailing '''
        json_text = match.group(1).strip().replace("'''", "").replace("```", "")
        return json_text
    return None

for i in range(500):
    try:
    # Generate a command
        command = query_deepseek("Generate a possible robotic command in natural language. You may randomly choose the tone and technical complexity of the command, remember that prople of differing backgrounds can be commanding the robot. Pick commands of varying complexity too, it can just be to simply move the end effector, or to pick up a cup and move it. Output the command only in this format \"**Command:** \"<command>\"\", and not the json")

        # print(command)
        print(extract_command_after_keyword(command))
        loading_bar(15)

        # Generate the corresponding JSON
        json_output = query_deepseek(f"Convert this command into JSON: '{command}'")

        print(json_output)
        # print(extract_json_after_json_keyword(json_output))

        try:
            data = {"command": extract_command_after_keyword(command), "json_output": json.loads(extract_json_after_json_keyword(json_output))}

            with open(os.path.join("json", f"command_{i}.jsonl"), "a") as f:
                f.write(json.dumps(data) + "\n")
            print("Generated Command", i)

        except:
            print("Error with", i, ", skipping")
    except:
        continue

