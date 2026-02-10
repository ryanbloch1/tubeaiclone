export type Database = {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string;
          email: string;
          full_name: string | null;
          avatar_url: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id: string;
          email: string;
          full_name?: string | null;
          avatar_url?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          email?: string;
          full_name?: string | null;
          avatar_url?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      projects: {
        Row: {
          id: string;
          user_id: string;
          title: string;
          description: string | null;
          status: string;
          topic: string | null;
          style: string | null;
          mode: string;
          temperature: number;
          word_count: number;
          image_count: number;
          video_length: string;
          selection: string | null;
          extra_context: string | null;
          video_type: string | null;
          property_type: string | null;
          property_address: string | null;
          property_price: number | null;
          bedrooms: number | null;
          bathrooms: number | null;
          square_feet: number | null;
          mls_number: string | null;
          property_features: unknown | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          title: string;
          description?: string | null;
          status?: string;
          topic?: string | null;
          style?: string | null;
          mode?: string;
          temperature?: number;
          word_count?: number;
          image_count?: number;
          video_length?: string;
          selection?: string | null;
          extra_context?: string | null;
          video_type?: string | null;
          property_type?: string | null;
          property_address?: string | null;
          property_price?: number | null;
          bedrooms?: number | null;
          bathrooms?: number | null;
          square_feet?: number | null;
          mls_number?: string | null;
          property_features?: unknown | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          title?: string;
          description?: string | null;
          status?: string;
          topic?: string | null;
          style?: string | null;
          mode?: string;
          temperature?: number;
          word_count?: number;
          image_count?: number;
          video_length?: string;
          selection?: string | null;
          extra_context?: string | null;
          video_type?: string | null;
          property_type?: string | null;
          property_address?: string | null;
          property_price?: number | null;
          bedrooms?: number | null;
          bathrooms?: number | null;
          square_feet?: number | null;
          mls_number?: string | null;
          property_features?: unknown | null;
          created_at?: string;
          updated_at?: string;
        };
      };
      scripts: {
        Row: {
          id: string;
          project_id: string;
          raw_script: string;
          edited_script: string;
          sanitized_script: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          project_id: string;
          raw_script: string;
          edited_script: string;
          sanitized_script?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          project_id?: string;
          raw_script?: string;
          edited_script?: string;
          sanitized_script?: string | null;
          created_at?: string;
          updated_at?: string;
        };
      };
    };
  };
};
