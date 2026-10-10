export type LectureStatus = 'unmarked' | 'understood' | 'missed' | 'upcoming'

export interface LectureRef {
  id: number
  order_index: number
  title: string
  status: LectureStatus
}

export interface Lecture extends LectureRef {
  created_at: string
  updated_at: string
}

export interface CourseSummary {
  last_understood_lecture: LectureRef | null
  upcoming_lecture: LectureRef | null
  missed_lectures: LectureRef[]
  unmarked_before_upcoming: LectureRef[]
}

export interface Course {
  id: number
  name: string
  created_at: string
  updated_at: string
}

export interface CourseListItem extends Course {
  lecture_count: number
  missed_count: number
}

export interface CourseDetail extends Course {
  lectures: Lecture[]
  summary: CourseSummary
}

export type MaterialStatus = 'uploaded' | 'processing' | 'ready' | 'failed'

export type MaterialKind = 'file' | 'notes'

export type MaterialFileType = 'pdf' | 'pptx' | 'ppt' | 'txt' | 'notes'

export interface Material {
  id: number
  lecture_id: number
  kind: MaterialKind
  file_type: MaterialFileType
  title: string
  original_filename: string | null
  file_size: number | null
  status: MaterialStatus
  error_message: string | null
  segment_count: number
  created_at: string
}
