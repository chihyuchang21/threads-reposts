export type IdeaStatus = "pending" | "approved" | "deleted";

export interface Repost {
  id: string;
  threads_post_id: string;
  original_author: string;
  original_content: string;
  reposted_at: string;
  scraped_at: string;
}

export interface Idea {
  id: string;
  repost_id: string;
  content: string;
  edited_content: string | null;
  extended_thoughts: string[];
  category: string | null;
  status: IdeaStatus;
  reviewed_at: string | null;
  created_at: string;
  repost?: Repost;
}
