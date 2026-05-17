<template>
  <el-dialog
    :title="isNewRow ? $t('dialog.add_row') : $t('dialog.edit_config')"
    :visible.sync="dialogVisible"
    width="520px"
    :close-on-click-modal="false"
    top="8vh"
  >
    <el-form :model="form" label-width="110px" size="small">
      <el-form-item v-for="col in columns" :key="col" :label="col">
        <el-input v-model="form[col]" :placeholder="$t('dialog.input_placeholder', { col })" clearable />
      </el-form-item>
    </el-form>
    <span slot="footer" class="dialog-footer">
      <el-button @click="close">{{ $t('dialog.cancel') }}</el-button>
      <el-button type="success" @click="save">{{ isNewRow ? $t('dialog.add') : $t('dialog.save') }}</el-button>
    </span>
  </el-dialog>
</template>

<script>
export default {
  name: 'EditDialog',
  props: {
    visible: { type: Boolean, default: false },
    isNewRow: { type: Boolean, default: false },
    columns: { type: Array, default: () => [] },
    form: { type: Object, default: () => ({}) }
  },
  computed: {
    dialogVisible: {
      get() { return this.visible },
      set(v) { this.$emit('update:visible', v) }
    }
  },
  methods: {
    close() { this.$emit('update:visible', false) },
    save() { this.$emit('save') }
  }
}
</script>

<style scoped>
.el-dialog__header {
  border-bottom: 1px solid var(--border-color); padding: 16px 24px;
}
.el-dialog__title { font-size: 16px; font-weight: 600; color: var(--text-primary); }
.el-dialog__body { padding: 20px 24px; }
.el-dialog__footer { border-top: 1px solid var(--border-color); padding: 12px 24px; }
</style>
