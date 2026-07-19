export type AnalysisCategory = "structure" | "timing" | "relationship" | "topic";
export type AnalysisStatus = "active" | "planned" | "paused";

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

export interface KlinePeriodInsight {
  headline: string;
  body: string;
  advice: string;
  trend_note: string;
  top_domains: string[];
  patience_domains: string[];
  bias_note: string;
  planet_label: string;
  house_title: string;
  dignity_label: string;
  dignity_note: string;
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
  insight?: KlinePeriodInsight | null;
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
  hero?: HeroSection | null;
  domains?: Record<string, DomainReport> | null;
  _analysis_evidence?: AnalysisEvidence | null;
  _transits?: TransitItem[] | null;
  _transits_fast?: TransitItem[] | null;
  _transits_slow?: TransitItem[] | null;
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
  characters?: CharacterProfilesData | null;
  planet_characters?: PlanetCharacterProfilesData | null;
}

export interface AngleView {
  angle_id: string;
  angle_label: string;
  narrative: string;
}

export interface InterpretationMatrix {
  primary_angle: AngleView;
  alternative_angles: AngleView[];
}

export interface DomainReport {
  domain: string;
  core_theme: string;
  tradition_weight: number;
  structure: string;
  psychology: string;
  suggestion: string;
  interpretation_matrix?: InterpretationMatrix;
  hero_bridge?: string;
}

export interface TransitItem {
  transiting_planet?: string;
  transiting_label: string;
  natal_planet?: string;
  natal_label: string;
  aspect_type?: string;
  aspect_label: string;
  orb: number;
  strength: number;
  is_applying: boolean;
  speed?: "fast" | "slow";
  highlight: string;
}

export interface HeroSection {
  core_theme: string;
  domain_summaries: Record<string, string>;
}

export interface AnalysisEvidence {
  planet_baselines: Record<string, any>;
  dignity_breakdown: Record<string, any>;
  house_infos?: Record<string, any>;
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
    fast_transits: TransitItem[];
  };
}

// ═══════════════════════════════════════════════════════════════
// 角色系统类型
// ═══════════════════════════════════════════════════════════════

export interface SignPersona {
  sign: string;
  name: string;
  archetype: string;
  element: string;
  modality: string;
  polarity: string;
  ruling_planet: string;
  essence: string;
  personality: string;
  voice_tone: string;
  social_mask: string;
  comfort_zone: string;
  stress_response: string;
  expertise_domains: string[];
  greeting_style: string;
  advice_approach: string;
  gift_to_user: string;
  challenge_to_user: string;
  keywords: string[];
  visual_color: string;
}

export interface CharacterProfile {
  sign: string;
  persona: SignPersona;
  presence_score: number;
  comfort_score: number;
  role_tag: string;           // "天赋角色" | "课题角色" | "核心角色" | "背景角色"
  planets_here: string[];
  planets_dignity: Record<string, string>;
  house_cusps_here: number[];
  is_ascendant: boolean;
  is_midheaven: boolean;
  storylines: string[];
  linked_domains: string[];
  personalized_greeting: string;
}

export interface CharacterProfilesData {
  characters: Record<string, CharacterProfile>;
  sorted_by_presence: Array<{
    sign: string;
    name: string;
    archetype: string;
    presence_score: number;
    role_tag: string;
  }>;
  core_characters: Array<{
    sign: string;
    name: string;
    presence_score: number;
    role_tag: string;
  }>;
  dormant_characters: Array<{
    sign: string;
    name: string;
  }>;
}

export interface FeaturedCharacter {
  sign: string;
  name: string;
  archetype: string;
  activation_score: number;
  reason: string;
  daily_message: string;
  suggested_topic: string;
  visual_color: string;
}

export interface DailyActivation {
  date: string;
  activation_scores: Record<string, number>;
  featured_characters: FeaturedCharacter[];
  lunar_note: string;
  firdaria_note: string;
  daily_theme: string;
}

export interface CharacterResponse {
  character: string;
  character_name: string;
  response: string;
  emotional_tone: string;
  suggested_followup: string;
}

export interface CouncilPerspective {
  character: string;
  character_name: string;
  archetype: string;
  perspective: string;
  visual_color: string;
}

export interface CouncilResponse {
  topic: string;
  topic_label: string;
  perspectives: CouncilPerspective[];
  synthesis: string;
}

export interface GrowthSummary {
  total_conversations: number;
  most_engaged_character: string;
  favorite_topics: Record<string, number>;
  streak_days: number;
  character_affinity: Record<string, number>;
  milestones_achieved: number;
  first_interaction_date: string;
  last_interaction_date: string;
}

export interface GrowthData {
  summary: GrowthSummary;
  milestones: Array<{
    milestone_type: string;
    sign: string;
    achieved_at: string;
    description: string;
  }>;
  recent_conversations: Array<{
    timestamp: string;
    sign: string;
    topic: string;
    user_message: string;
    character_response: string;
    emotional_context: string;
  }>;
}

// ── v2.0 行星人格角色系统 (对标万象有灵十神模型) ──

export interface PlanetPersona {
  planet: string;
  name_zh: string;
  archetype_zh: string;
  element: string;
  nature: string;
  domain_zh: string;
  essence: string;
  personality: string;
  voice_tone: string;
  social_mask: string;
  comfort_zone: string;
  stress_response: string;
  expertise_domains: string[];
  greeting_style: string;
  advice_approach: string;
  gift_to_user: string;
  challenge_to_user: string;
  keywords: string[];
  visual_color: string;
  symbol: string;
  ruling_signs_zh: string;
}

export interface SignFlavorOverlay {
  sign: string;
  sign_name: string;
  element: string;
  modality: string;
  polarity: string;
  voice_tone: string;
  personality_snippet: string;
  visual_color: string;
  keywords: string[];
}

export interface HouseContext {
  house: number;
  title: string;
  domain: string;
  topic: string;
}

export interface PlanetCharacterProfile {
  planet: string;
  persona: PlanetPersona;
  core_strength: number;
  sign: string;
  sign_label: string;
  house: number;
  house_label: string;
  dignity_code: string;
  dignity_label: string;
  role_tag: string;
  sign_flavor: SignFlavorOverlay;
  house_context: HouseContext;
  is_chart_ruler: boolean;
  personalized_greeting: string;
  linked_domains: string[];
}

export interface PlanetCharacterProfilesData {
  planet_characters: Record<string, PlanetCharacterProfile>;
  main_character: PlanetCharacterProfile;
  sorted_by_strength: Array<{
    planet: string;
    name_zh: string;
    archetype_zh: string;
    core_strength: number;
    role_tag: string;
    symbol: string;
  }>;
  core_planets: Array<{
    planet: string;
    name_zh: string;
    core_strength: number;
    role_tag: string;
  }>;
}

export interface FeaturedPlanet {
  planet: string;
  name_zh: string;
  archetype_zh: string;
  symbol: string;
  sign: string;
  activation_score: number;
  reason: string;
  daily_message: string;
  suggested_topic: string;
  visual_color: string;
}

export interface PlanetDailyActivation {
  date: string;
  activation_scores: Record<string, number>;
  featured_planets: FeaturedPlanet[];
  main_character: FeaturedPlanet;
  daily_theme: string;
  lunar_note: string;
  firdaria_note: string;
}
