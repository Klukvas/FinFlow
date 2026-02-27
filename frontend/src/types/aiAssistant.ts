export interface AnalysisSection {
  title: string;
  content: string;
  priority: "high" | "medium" | "low";
}

export interface AnalysisResponse {
  prompt_id: string;
  sections: AnalysisSection[];
  cached: boolean;
  language: string;
}

export interface AnalysisRequest {
  prompt_id: string;
  language: string;
}

export interface PromptMetadata {
  id: string;
  block: string;
  title_key: string;
  description_key: string;
  icon: string;
}

export interface PromptBlockMetadata {
  block: string;
  title_key: string;
  prompts: PromptMetadata[];
}
