export interface ApiUser {
  id: string;
  clerk_user_id: string;
  role: string;
  email: string;
  full_name: string;
  phone_number: string | null;
}