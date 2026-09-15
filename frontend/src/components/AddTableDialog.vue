<template>
  <el-dialog
    class="mml-ui"
    :title="$t(table ? 'overview.edit_table_title' : 'overview.add_table_title')"
    v-model="dialogVisible"
    width="min(680px, 94vw)"
    :close-on-click-modal="false"
    @closed="reset"
  >
    <el-form ref="formRef" :model="form" label-position="top">
      <el-form-item
        :label="$t('overview.table_name')"
        prop="tableName"
        :rules="[{ required: true, whitespace: true, message: $t('overview.table_name_required'), trigger: 'blur' }]"
      >
        <el-input v-model="form.tableName" :placeholder="$t('overview.add_table_name_placeholder')" />
      </el-form-item>

      <div class="field-heading">
        <span>{{ $t("overview.fields") }}</span>
        <el-button size="small" @click="addField">{{ $t("overview.add_field") }}</el-button>
      </div>
      <el-alert
        v-if="table"
        class="edit-warning"
        type="warning"
        :closable="false"
        :title="$t('overview.edit_table_warning')"
      />
      <div v-for="(field, index) in form.fields" :key="field.id" class="field-row">
        <el-form-item
          :prop="`fields.${index}.name`"
          :rules="[{ required: true, whitespace: true, message: $t('overview.field_name_required'), trigger: 'blur' }]"
        >
          <el-input v-model="field.name" :placeholder="$t('overview.field_name')" />
        </el-form-item>
        <el-form-item
          :prop="`fields.${index}.dataType`"
          :rules="[{ required: true, message: $t('overview.data_type_required'), trigger: 'change' }]"
        >
          <el-select v-model="field.dataType" :placeholder="$t('overview.data_type')">
            <el-option
              v-for="option in dataTypeOptions"
              :key="option.value"
              :label="$t(option.label)"
              :value="option.value"
            />
          </el-select>
        </el-form-item>
        <el-button
          class="remove-field"
          type="danger"
          link
          :disabled="form.fields.length === 1"
          @click="removeField(index)"
        >
          {{ $t("overview.remove_field") }}
        </el-button>
      </div>
      <el-alert v-if="duplicateField" type="error" :closable="false" :title="$t('overview.duplicate_field')" />
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">{{ $t("dialog.cancel") }}</el-button>
      <el-button type="primary" @click="submit">{{ $t(table ? "dialog.save" : "dialog.add") }}</el-button>
    </template>
  </el-dialog>
</template>

<script>
let nextFieldId = 1;

const newField = () => ({ id: nextFieldId++, name: "", dataType: "string", originalName: null });

export default {
  name: "AddTableDialog",
  props: {
    visible: { type: Boolean, default: false },
    table: { type: Object, default: null },
  },
  emits: ["update:visible", "submit"],
  data() {
    return {
      form: { tableName: "", fields: [newField()] },
      dataTypeOptions: [
        { value: "string", label: "overview.type_string" },
        { value: "integer", label: "overview.type_integer" },
        { value: "decimal", label: "overview.type_decimal" },
        { value: "boolean", label: "overview.type_boolean" },
      ],
    };
  },
  computed: {
    dialogVisible: {
      get() {
        return this.visible;
      },
      set(value) {
        this.$emit("update:visible", value);
      },
    },
    duplicateField() {
      const names = this.form.fields.map((field) => field.name.trim()).filter(Boolean);
      return new Set(names).size !== names.length;
    },
  },
  watch: {
    visible(value) {
      if (value) this.$nextTick(this.populate);
    },
    table: {
      deep: true,
      handler() {
        if (this.visible) this.$nextTick(this.populate);
      },
    },
  },
  methods: {
    addField() {
      this.form.fields.push(newField());
    },
    removeField(index) {
      if (this.form.fields.length > 1) this.form.fields.splice(index, 1);
    },
    reset() {
      this.form = { tableName: "", fields: [newField()] };
      this.$refs.formRef?.clearValidate();
    },
    populate() {
      if (!this.table) {
        this.reset();
        return;
      }
      this.form = {
        tableName: this.table.table_name,
        fields: this.table.columns.map((name) => ({
          id: nextFieldId++,
          name,
          originalName: name,
          dataType: this.table.column_types?.[name] || "",
        })),
      };
    },
    async submit() {
      const valid = await this.$refs.formRef.validate().catch(() => false);
      if (!valid || this.duplicateField) return;
      this.$emit("submit", {
        originalTableName: this.table?.table_name || null,
        tableName: this.form.tableName.trim(),
        fields: this.form.fields.map((field) => ({
          name: field.name.trim(),
          dataType: field.dataType,
          originalName: field.originalName,
        })),
      });
    },
  },
};
</script>

<style scoped>
.field-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  font-weight: 600;
}
.edit-warning {
  margin-bottom: 14px;
}
.field-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 180px auto;
  gap: 12px;
  align-items: start;
}
.field-row :deep(.el-select) {
  width: 100%;
}
.remove-field {
  margin-top: 7px;
}
@media (max-width: 620px) {
  .field-row {
    grid-template-columns: minmax(0, 1fr) 140px;
  }
  .remove-field {
    grid-column: 1 / -1;
    justify-self: end;
    margin-top: -14px;
  }
}
</style>
