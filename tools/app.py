import json
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

client = genai.Client()

#TOOLS
def timetable_analysis(day: str, timetable_data: str) -> str:
    """
    Analyzes a raw timetable string to find classes for a specific day.
    Args:
        day: The day of the week to check (e.g., 'Monday', 'Tuesday').
    """
    with open('data.json', 'r') as file:
        data = json.load(file)
    
    day_key = day.strip().capitalize()
    schedule = data.get("timetable_data", {}).get(day_key, [])
    
    if not schedule:
        return f"No classes found or scheduled for {day_key}."
        
    result = f"Classes for {day_key}:\n"
    for item in schedule:
        result += f"- {item['time']}: {item['subject']} in {item['room']}\n"
    return result


def calculate_attendance_percentage(subject_code: str) -> str:
    """
    Calculates the exact attendance percentage and warning status for a course.
    Args:
        subject_code: The exact string code of the course (e.g., 'CS101', 'MA102', 'PH103').
    """
    with open('data.json', 'r') as file:
        data = json.load(file)
        
    code = subject_code.upper().strip()
    stats = data.get("attendance_stats", {}).get(code)
    
    if not stats:
        return f"Error: Subject '{subject_code}' not found."
        
    pct = (stats["attended"] / stats["total"]) * 100
    status = "Safe" if pct >= 75 else "Low Attendance Warning"
    return f"{stats['subject_name']} ({code}) Attendance is {pct:.2f}%. Status: {status}."

def mark_attendance(subject_code: str, status: str) -> str:
    """Marks a student as Present or Absent for a class."""
    
    with open('data.json', 'r') as file:
        data = json.load(file)
        
    code = subject_code.upper().strip()
    stats = data["attendance_stats"][code]

    stats["total"] += 1
    if status.lower() == "present":
        stats["attended"] += 1

    with open('data.json', 'w') as file:
        json.dump(data, file, indent=4)

    return f"Logged: {subject_code} marked as {status}."


if __name__ == "__main__":

    tools_map = {
        "timetable_analysis": timetable_analysis,
        "calculate_attendance_percentage": calculate_attendance_percentage,
        "mark_attendance": mark_attendance
    }

    user_query = ""
    print("======COLLEGE AI ASSISTANT======")
    print("The assistant can help you with your timetable analysis, attendance calculation, or in marking of attendance.")
    print("Note: Data is provided via the 'data.json' file.")
    print("Type 'exit' to quit the program.")
    while user_query.lower() != "exit":
        user_query = input("Ask the College Assistant: ")

        if user_query.lower() == "exit":
            print("Shutting down...")
            break
        else:
            with open('data.json', 'r') as file:
                data = json.load(file)
                
        
            prompt = (
                f"User Question: {user_query}\n\n"
                f"Context Database:\n"
                f"Timetable Details: {json.dumps(data.get('timetable_data'))}\n"
                f"Attendance Statistics: {json.dumps(data.get('attendance_stats'))}"
            )
            

            response = client.models.generate_content(
                model='gemini-3.5-flash-lite',
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=list(tools_map.values()),
                    system_instruction="You are a College Assistant. Call the correct tool based on what the user wants.",
                    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                )
            )
            
            tool_used = "NONE"
            tool_called = False
            if response.function_calls:
                for call in response.function_calls:
                    if call.name in tools_map:
                        tool_called = True
                        print(f"🔧 [Tool Used]: {call.name}")
                        
                        tool_result = tools_map[call.name](**call.args)
                        
                        final_prompt = (
                            f"{prompt}\n\n"
                            f"[System Update: The tool '{call.name}' was executed successfully.\n"
                            f"Result returned from local database]:\n{tool_result}\n\n"
                            f"Please provide the clean final answer text for the student based on this result."
                        )
                        
                        final_response = client.models.generate_content(
                            model='gemini-3.5-flash-lite',
                            contents=final_prompt
                        )
                        print(f"AI Output: {final_response.text}\n")
                        break
            
            if not tool_called:
                print("🔧 [Tool Used]: None (Direct Answer)")
                print(f"AI Output: {response.text}\n")
