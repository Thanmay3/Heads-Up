import { request } from './client'
import type { Material } from './types'

export function listMaterials(lectureId: number): Promise<Material[]> {
  return request<Material[]>(`/lectures/${lectureId}/materials`)
}

export function uploadMaterial(lectureId: number, file: File): Promise<Material> {
  const form = new FormData()
  form.append('file', file)
  return request<Material>(`/lectures/${lectureId}/materials`, {
    method: 'POST',
    body: form,
    // No Content-Type header: the browser must set it with the multipart boundary.
    headers: {},
  })
}

export function addNotes(
  lectureId: number,
  title: string,
  content: string,
): Promise<Material> {
  return request<Material>(`/lectures/${lectureId}/notes`, {
    method: 'POST',
    body: JSON.stringify({ title, content }),
  })
}

export function deleteMaterial(id: number): Promise<void> {
  return request<void>(`/materials/${id}`, { method: 'DELETE' })
}
