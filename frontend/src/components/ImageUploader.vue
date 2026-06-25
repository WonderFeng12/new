<template>
  <div>
    <el-upload
      :multiple="true"
      :auto-upload="false"
      :show-file-list="true"
      :on-change="handleChange"
      :file-list="fileList"
      list-type="picture-card"
      accept=".jpg,.jpeg,.png,.bmp"
    >
      <el-icon><Plus /></el-icon>
      <template #tip>
        <div style="font-size:12px;color:#999">支持 JPG/PNG/BMP，自动压缩</div>
      </template>
    </el-upload>

    <div v-if="uploading" style="margin-top:10px">
      <el-progress :percentage="uploadProgress" />
    </div>

    <div v-if="uploadedFiles.length" style="margin-top:10px">
      <el-tag v-for="f in uploadedFiles" :key="f.path" closable @close="removeUploaded(f)" style="margin:2px">
        {{ f.original_name }} (压缩 {{ f.saved_percent }}%)
      </el-tag>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { uploadImages } from '../../api/upload'

const emit = defineEmits(['update:modelValue'])
const props = defineProps({
  modelValue: { type: Array, default: () => [] },
})

const fileList = ref([])
const uploadedFiles = ref([...props.modelValue])
const uploading = ref(false)
const uploadProgress = ref(0)

async function handleChange(file) {
  const rawFiles = fileList.value.map(f => f.raw).filter(Boolean)
  if (!rawFiles.length) return
  uploading.value = true
  uploadProgress.value = 50
  try {
    const res = await uploadImages(rawFiles)
    uploadedFiles.value.push(...res.data)
    emit('update:modelValue', uploadedFiles.value)
    fileList.value = []
    ElMessage.success(`上传 ${res.data.length} 个文件成功`)
  } catch {
    ElMessage.error('上传失败')
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }
}

function removeUploaded(file) {
  uploadedFiles.value = uploadedFiles.value.filter(f => f.path !== file.path)
  emit('update:modelValue', uploadedFiles.value)
}
</script>
