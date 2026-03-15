export interface User {
  ID: number
  user_login: string
  user_email: string
  user_nicename: string
  display_name: string
  user_url: string
  user_registered: string
}

export interface AuthState {
  token: string | null
  user: User | null
}

export interface Term {
  term_id: number
  term_taxonomy_id: number
  name: string
  slug: string
  description: string
  parent: number
  count: number
  taxonomy: string
}

export interface Author {
  ID: number
  display_name: string
  user_login: string
}

export interface Post {
  ID: number
  post_author: number
  author: Author | null
  post_title: string
  post_content: string
  post_excerpt: string
  post_status: 'publish' | 'draft' | 'private' | 'trash' | 'pending' | 'future'
  post_name: string
  post_type: string
  post_date: string
  post_modified: string
  comment_status: 'open' | 'closed'
  ping_status: 'open' | 'closed'
  post_password: string
  menu_order: number
  categories: Term[]
  tags: Term[]
  featured_image_url: string | null
  featured_image_id: number | null
  comment_count: number
}

export interface PostListOut {
  items: Post[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface PostCreatePayload {
  post_title: string
  post_content: string
  post_excerpt?: string
  post_status: string
  post_name?: string
  comment_status?: string
  post_type?: string
  category_ids?: number[]
  tag_ids?: number[]
  featured_image_id?: number | null
}

export interface PostUpdatePayload extends Partial<PostCreatePayload> {}

export interface Media {
  ID: number
  post_title: string
  post_mime_type: string
  guid: string
  post_date: string
  post_author: number
  file_url: string
  thumbnail_url: string | null
  alt_text: string
  caption: string
  file_size: number | null
}

export interface MediaListOut {
  items: Media[]
  total: number
  page: number
  per_page: number
}

export interface Comment {
  comment_ID: number
  comment_post_ID: number
  comment_author: string
  comment_author_email: string
  comment_author_url: string
  comment_date: string
  comment_content: string
  comment_approved: string
  comment_parent: number
  user_id: number
}

export interface CommentListOut {
  items: Comment[]
  total: number
  page: number
  per_page: number
}

export interface TermListOut {
  items: Term[]
  total: number
}

export interface DashboardStats {
  posts: { published: number; draft: number }
  pages: { published: number }
  comments: { approved: number; pending: number }
  media: number
  categories: number
  tags: number
  recent_posts: Array<{ ID: number; post_title: string; post_date: string; post_status: string }>
}

export type PostStatus = 'publish' | 'draft' | 'private' | 'pending' | 'trash'
