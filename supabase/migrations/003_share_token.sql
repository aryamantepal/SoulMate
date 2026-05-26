-- Adds share_token column to profiles table for public anonymous taste-sharing
ALTER TABLE public.profiles ADD COLUMN IF NOT EXISTS share_token TEXT UNIQUE;
