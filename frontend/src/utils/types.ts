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
    gender?: string | null;
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
    signature?: string;
    keywords?: string[];
    key_signals?: Array<{
      label: string;
      value: string;
      hint?: string;
    }>;
    layers?: Array<{
      key: string;
      title: string;
      headline: string;
      summary: string;
      evidence?: string[];
      focus_cards?: Array<{
        label: string;
        value: string;
        hint?: string;
      }>;
      points: string[];
    }>;
    self_profile?: {
      title?: string;
      summary?: string;
      baseline?: string;
      cards?: Array<{
        label: string;
        value: string;
        hint?: string;
      }>;
      evidence?: string[];
      points?: string[];
    };
    career_blueprint?: {
      title?: string;
      summary?: string;
      selection_prompt?: string;
      method_tags?: string[];
      paths?: Array<{
        key: string;
        title: string;
        fit_score: number;
        fit_label: string;
        track_label?: string;
        track_reason?: string;
        summary: string;
        risk_summary?: string;
        sources?: string[];
        roles?: string[];
        selection_tags?: string[];
        evidence?: string[];
        theory?: string[];
        points?: string[];
      }>;
    };
    theory_basis?: {
      title?: string;
      summary?: string;
      chips?: string[];
      points?: string[];
    };
    question_sections?: Array<{
      key: string;
      question: string;
      answer: string;
      takeaways?: string[];
      risks?: string[];
      actions?: string[];
      evidence?: string[];
    }>;
    [key: string]: any;
  } | null;
  advanced_patterns?: {
    summary?: string;
    house_rulers?: Array<{
      house: number;
      title: string;
      sign: string;
      sign_label?: string;
      ruler: string;
      ruler_label: string;
      ruler_house: number;
      ruler_house_title: string;
      ruler_sign: string;
      ruler_sign_label?: string;
      dignity: string;
      dignity_label?: string;
      adult_meaning?: string;
      notation: string;
      line: string;
      late_five_applied?: boolean;
      late_five_distance?: number;
      late_five_note?: string | null;
      flight_summary?: string | null;
      flight_positive?: string | null;
      flight_negative?: string | null;
      flight_tone?: string | null;
      flight_tone_label?: string | null;
      flight_note?: string | null;
      flight_target_title?: string | null;
      flight_target_theme?: string | null;
    }>;
    ruler_groups?: Array<{
      ruler: string;
      ruler_label: string;
      houses: number[];
      house_titles: string[];
      notation: string;
      line: string;
      ruler_house: number;
      ruler_house_title: string;
      ruler_sign: string;
      ruler_sign_label?: string;
      dignity: string;
      dignity_label?: string;
    }>;
    reception_groups?: Array<{
      receiver: string;
      receiver_label: string;
      receiver_house: number;
      receiver_house_title: string;
      receiver_sign: string;
      receiver_sign_label?: string;
      guests: Array<{
        planet: string;
        label: string;
        house: number;
        house_title: string;
        sign: string;
        sign_label?: string;
      }>;
      line: string;
      summary: string;
    }>;
    mutual_receptions?: Array<{
      pair: string[];
      labels: string[];
      line: string;
      summary: string;
    }>;
    derived_houses?: Array<{
      base_house: number;
      base_label: string;
      summary: string;
      links: Array<{
        label: string;
        derived_house: number;
        radical_house: number;
        title: string;
        adult_meaning?: string;
        line: string;
        ruler_line: string;
      }>;
    }>;
    core_threads?: Array<{
      house: number;
      title: string;
      summary: string;
      points: string[];
    }>;
    pattern_readings?: Array<{
      key: string;
      title: string;
      summary: string;
      risk_summary?: string;
      evidence: string[];
      points: string[];
    }>;
    case_themes?: Array<{
      key: string;
      title: string;
      summary: string;
      evidence: string[];
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

export interface LunarReturnDailyDegree {
  date: string;
  time_local: string;
  time_utc: string;
  orb: number;
  separation: number;
}

export interface LunarReturnWindow {
  planet: string;
  planet_label: string;
  aspect_key: string;
  aspect_angle: number;
  aspect_label: string;
  orb_limit: number;
  start_time_local: string;
  end_time_local: string;
  start_time_utc: string;
  end_time_utc: string;
  exact_time_local: string;
  exact_time_utc: string;
  exact_orb: number;
  exact_separation: number;
  daily_degrees: LunarReturnDailyDegree[];
}

export interface MonthlyLunarReturnReport {
  meta: {
    generated_at: string;
    engine_version: string;
  };
  user_info: {
    gender?: string | null;
    birth_time_local: string;
    birth_time_utc: string;
    lat: number;
    lon: number;
    timezone: string;
    is_day_chart: boolean;
  };
  reference: {
    current_date_utc: string;
    current_date_local: string;
    timezone_offset: number;
  };
  natal_chart?: LifeReport["natal_chart"];
  lunar_return: {
    cycle_label: string;
    return_time_local: string;
    return_time_utc: string;
    next_return_time_local: string;
    next_return_time_utc: string;
    cycle_start_local: string;
    cycle_end_local: string;
    cycle_start_utc: string;
    cycle_end_utc: string;
    moon_windows: LunarReturnWindow[];
    chart: LifeReport["natal_chart"];
  };
}
