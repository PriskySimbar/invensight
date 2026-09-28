export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "https://invensight.kubeletto.app";

export interface AnalyzeResponse {
  sql_query: string;
  data: Record<string, any>[];
  summary: string;
  is_error: boolean;
}

export interface AnalyzeError {
  message: string;
  details?: string;
}

export async function analyzeQuestion(question: string): Promise<AnalyzeResponse> {
  try {
    console.log("API Request:", { url: `${API_BASE_URL}/api/v1/analyze`, question });
    
    const response = await fetch(`${API_BASE_URL}/api/v1/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ question }),
    });

    console.log("API Response status:", response.status, "OK:", response.ok);

    if (!response.ok) {
      const errorText = await response.text();
      console.error("API Error response text:", errorText);
      try {
        const errorData = JSON.parse(errorText);
        throw new Error(errorData.detail || errorData.message || `HTTP error! status: ${response.status}`);
      } catch {
        throw new Error(errorText || `HTTP error! status: ${response.status}`);
      }
    }

    const data = await response.json();
    console.log("API Success response:", data);
    return data;
  } catch (error) {
    console.error("API Request failed:", error);
    const errorMessage = error instanceof Error ? error.message : String(error);
    console.error("Error message:", errorMessage);
    throw new Error(errorMessage || "Failed to connect to the server");
  }
}
