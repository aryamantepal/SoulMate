-- Adds an optional named collection ("folder") to each saved shoe.
-- NULL = uncategorized. A shoe belongs to at most one collection.
ALTER TABLE public.saved_shoes ADD COLUMN IF NOT EXISTS collection TEXT;
