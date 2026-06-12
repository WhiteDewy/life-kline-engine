export type AnalysisCategory = "structure" | "timing" | "relationship" | "topic";
export type AnalysisStatus = "active" | "planned";

export interface AnalysisDefinition {
  key: string;
  title: string;
  tagline: string;
  description: string;
  category: AnalysisCategory;
  status: AnalysisStatus;
  subjects_count: number;
  required_inputs: string[];
  engines: string[];
  modules: string[];
  primary_cta: string;
  output_route: string;
}

export interface AnalysisResponse<T> {
  status: string;
  report_id?: string;
  analysis?: AnalysisDefinition;
  data: T;
}

export interface AstrologyInfo {
  sign: string;
  sign_label?: string;
  house: number;
  house_title?: string;
  dignity: string;
  dignity_label?: string;
  major: string;
  sub: string;
  major_score?: number;
  sub_score?: number;
  aspect_signature?: string[];
  composition?: Array<{
    planet: string;
    weight: number;
    score: number;
  }>;
  dominant_trend?: string;
}

export interface KPoint {
  x: string;
  open: number;
  close: number;
  low: number;
  high: number;
  score?: number;
  title?: string;
  summary?: string;
  themes?: string[];
  opportunities?: string[];
  cautions?: string[];
  action_focus?: string[];
  astrology?: AstrologyInfo;
}

export interface DomainScores {
  overall: number;
  career: number;
  wealth: number;
  relationship: number;
  health: number;
  family: number;
}

export interface DomainPoint {
  x: string;
  scores: DomainScores;
}

export interface KlinePeriod {
  index: number;
  timing: {
    start_age: number;
    end_age: number;
    start_date: string;
    end_date: string;
    duration_years: number;
  };
  lords: {
    major: string;
    sub: string | null;
  };
  trend: {
    bonus_coefficient: number;
    type: string;
  };
  domains: DomainScores;
  astrology: {
    sign: string;
    sign_label?: string;
    house: number;
    house_title?: string;
    dignity: string;
    dignity_label?: string;
    major_score?: number;
    sub_score?: number;
    aspect_signature?: string[];
  };
  title?: string;
  summary?: string;
  themes?: string[];
  opportunities?: string[];
  cautions?: string[];
  action_focus?: string[];
  type: string;
}

export interface LifeReport {
  meta: {
    generated_at: string;
    engine_version: string;
  };
  user_info: {
    birth_time_local: string;
    birth_time_utc: string;
    lat: number;
    lon: number;
    timezone: string;
    is_day_chart: boolean;
  };
  kline_data: {
    periods: KlinePeriod[];
  };
  natal_chart?: {
    ascendant?: {
      sign: string;
      sign_label?: string;
      degree: number;
    };
    houses?: Array<{
      house: number;
      sign: string;
      sign_label?: string;
      degree: number;
      title?: string;
    }>;
    sect?: string;
    sect_label?: string;
    chart_ruler?: string;
    chart_ruler_label?: string;
    signature?: string;
    planets?: Record<string, any>;
    dominant_planets?: Array<Record<string, any>>;
    pressure_points?: Array<Record<string, any>>;
    house_emphasis?: Array<Record<string, any>>;
    major_aspects?: Array<Record<string, any>>;
    [key: string]: any;
  } | null;
  current_phase?: Record<string, any> | null;
  life_model?: Record<string, any> | null;
  natal_blueprint?: {
    role_title?: string;
    summary?: string;
    keywords?: string[];
    layers?: Array<{
      key: string;
      title: string;
      headline: string;
      summary: string;
      points: string[];
    }>;
    [key: string]: any;
  } | null;
  timeline_validation?: {
    mode?: string;
    title?: string;
    summary?: string;
    events?: Array<{
      date_label: string;
      title: string;
      category: string;
      age_label: string;
      phase_title: string;
      phase_range: string;
      phase_lords: string;
      phase_summary: string;
      validation: string;
      reading: string;
    }>;
    [key: string]: any;
  } | null;
}
