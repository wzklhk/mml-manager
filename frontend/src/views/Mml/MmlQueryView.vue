<template>
  <div class="mml-query mml-ui" :class="{ 'sidebar-collapsed': sidebarCollapsed }">
    <VueHeader
      :menu-active="menuActive"
      :selected-table="selectedTable"
      :snapshots="snapshots"
      :active-snapshot-id="activeSnapshotId"
      @menu-select="handleMenuSelect"
      @upload-start="handleUploadStart"
      @upload-success="handleUploadSuccess"
      @upload-error="handleUploadError"
      @snapshot-create="createConfiguration"
      @compare="compareDialogVisible = true"
      @snapshot-change="switchSnapshot"
      @snapshot-delete="deleteSnapshot"
      @logo-click="backToOverview"
    />

    <el-container
      v-loading="uploading"
      element-loading-text=" importing..."
      element-loading-spinner="el-icon-loading"
      style="flex: 1; overflow: hidden"
    >
      <Sidebar
        :selected-table="selectedTable"
        :tables="tables"
        :collapsed="sidebarCollapsed"
        @toggle-sidebar="sidebarCollapsed = !sidebarCollapsed"
        @select-table="enterTable"
      />

      <el-main class="vue-main">
        <TableOverview
          v-show="!selectedTable"
          v-model="tableSearch"
          :tables="pagedTables"
          :can-export="tables.length > 0"
          :can-manage-tables="Boolean(activeSnapshotId)"
          :pagination="tablePagination"
          @enter-table="enterTable"
          @add-table="addTable"
          @delete-table="deleteTable"
          @refresh="loadTables"
          @export-all="exportAll"
          @sort="handleOverviewSort"
          @page-change="handleTablePageChange"
          @size-change="handleTableSizeChange"
        />

        <TableDetail
          ref="tableDetail"
          v-show="selectedTable"
          :table-name="selectedTable"
          :columns="currentColumns"
          :configs="configs"
          :loading="loading"
          :selected-rows="selectedRows"
          :pagination="pagination"
          @sort-change="handleSortChange"
          @filter-change="handleFilterChange"
          @selection-change="handleSelectionChange"
          @page-change="handlePageChange"
          @size-change="handleSizeChange"
          @batch-delete="batchDelete"
          @batch-export="batchExport"
          @add-row="showAddRowDialog"
          @edit-row="handleEdit"
          @delete-row="handleDelete"
        />
      </el-main>
    </el-container>

    <EditDialog
      v-model:visible="editDialogVisible"
      :is-new-row="isNewRow"
      :columns="currentColumns"
      :form="editForm"
      @save="saveEdit"
    />
    <CompareDialog v-model:visible="compareDialogVisible" />
    <ExportPreviewDialog
      v-model:visible="exportPreviewVisible"
      :loading="exporting"
      :format="pendingExport?.format || ''"
      :scope="pendingExport?.scope || 'selected'"
      :count="pendingExport?.count || 0"
      :rows="pendingExport?.rows || []"
      :columns="pendingExport?.columns || []"
      :tables="pendingExport?.tables || []"
      @confirm="confirmExport"
    />
  </div>
</template>

<script>
import VueHeader from "../../components/VueHeader.vue";
import Sidebar from "../../components/Sidebar.vue";
import TableOverview from "../../components/TableOverview.vue";
import TableDetail from "../../components/TableDetail.vue";
import EditDialog from "../../components/EditDialog.vue";
import CompareDialog from "../../components/CompareDialog.vue";
import ExportPreviewDialog from "../../components/ExportPreviewDialog.vue";
import apiClient from "../../api/client";

export default {
  name: "MmlQueryView",
  components: { VueHeader, Sidebar, TableOverview, TableDetail, EditDialog, CompareDialog, ExportPreviewDialog },
  data() {
    return {
      configs: [],
      tables: [],
      snapshots: [],
      activeSnapshotId: "",
      selectedTable: "",
      currentColumns: [],
      loading: false,
      tableSearch: "",
      selectedRows: [],
      sidebarCollapsed: false,
      pagination: { page: 1, pageSize: 20, total: 0 },
      tablePagination: { page: 1, pageSize: 20, total: 0 },
      editDialogVisible: false,
      isNewRow: false,
      editForm: {},
      sort: { prop: null, order: null },
      columnFilters: {},
      uploading: false,
      compareDialogVisible: false,
      exportPreviewVisible: false,
      exporting: false,
      pendingExport: null,
    };
  },
  computed: {
    menuActive() {
      return this.selectedTable ? "detail" : "overview";
    },
    filteredTables() {
      if (!this.tableSearch) return this.tables;
      const q = this.tableSearch.toLowerCase();
      return this.tables.filter((t) => t.table_name.toLowerCase().includes(q));
    },
    pagedTables() {
      const start = (this.tablePagination.page - 1) * this.tablePagination.pageSize;
      return this.filteredTables.slice(start, start + this.tablePagination.pageSize);
    },
  },
  watch: {
    tableSearch() {
      this.tablePagination.page = 1;
      this.syncTablePagination();
    },
    filteredTables() {
      this.syncTablePagination();
    },
  },
  mounted() {
    this.loadSnapshots();
    this.loadTables();
  },
  methods: {
    handleMenuSelect(index) {
      if (index === "overview") this.backToOverview();
    },
    handleOverviewSort({ prop, order }) {
      if (!prop || !order) return;
      const dir = order === "ascending" ? "asc" : "desc";
      this.tables.sort((a, b) => {
        let va = a[prop],
          vb = b[prop];
        if (typeof va === "string") va = va.toLowerCase();
        if (typeof vb === "string") vb = vb.toLowerCase();
        if (va < vb) return dir === "asc" ? -1 : 1;
        if (va > vb) return dir === "asc" ? 1 : -1;
        return 0;
      });
    },

    syncTablePagination() {
      this.tablePagination.total = this.filteredTables.length;
      const lastPage = Math.max(1, Math.ceil(this.tablePagination.total / this.tablePagination.pageSize));
      if (this.tablePagination.page > lastPage) this.tablePagination.page = lastPage;
    },
    handleTablePageChange(page) {
      this.tablePagination.page = page;
    },
    handleTableSizeChange(size) {
      this.tablePagination.pageSize = size;
      this.tablePagination.page = 1;
      this.syncTablePagination();
    },

    handleSelectionChange(rows) {
      this.selectedRows = rows;
    },
    clearSelectedRows() {
      this.selectedRows = [];
      this.$nextTick(() => this.$refs.tableDetail?.clearSelection());
    },

    async loadSnapshots() {
      try {
        const res = await apiClient.get("/api/snapshots");
        this.snapshots = res.data.snapshots;
        this.activeSnapshotId = res.data.active_id || "";
      } catch (e) {
        this.$message.error(this.$t("msg.load_snapshots_fail", { msg: e.message }));
      }
    },

    async createConfiguration() {
      try {
        const result = await this.$prompt(
          this.$t("header.new_config_prompt"),
          this.$t("header.new_config_title"),
          {
            confirmButtonText: this.$t("dialog.add"),
            cancelButtonText: this.$t("dialog.cancel"),
            inputPlaceholder: this.$t("header.new_config_placeholder"),
            inputValidator: (value) => Boolean(value?.trim()) || this.$t("header.config_name_required"),
          },
        );
        const response = await apiClient.post("/api/snapshots", { name: result.value.trim() });
        this.activeSnapshotId = response.data.snapshot.id;
        this.backToOverview();
        await this.loadSnapshots();
        await this.loadTables();
        this.$message.success(this.$t("msg.create_config_success"));
      } catch (e) {
        if (e === "cancel" || e === "close") return;
        this.$message.error(this.$t("msg.create_config_fail", { msg: e.response?.data?.error || e.message }));
      }
    },

    async switchSnapshot(snapshotId) {
      if (!snapshotId || snapshotId === this.activeSnapshotId) return;
      try {
        await apiClient.post(`/api/snapshots/${snapshotId}/activate`);
        this.activeSnapshotId = snapshotId;
        this.backToOverview();
        await this.loadTables();
      } catch (e) {
        this.$message.error(this.$t("msg.switch_snapshot_fail", { msg: e.message }));
      }
    },

    deleteSnapshot(snapshotId) {
      const snapshot = this.snapshots.find((item) => item.id === snapshotId);
      this.$confirm(
        this.$t("confirm.delete_snapshot_content", { name: snapshot?.name || "" }),
        this.$t("confirm.delete_snapshot_title"),
        {
          confirmButtonText: this.$t("confirm.btn_confirm"),
          cancelButtonText: this.$t("confirm.btn_cancel"),
          type: "warning",
        },
      )
        .then(async () => {
          try {
            const response = await apiClient.post(`/api/snapshots/${snapshotId}/delete`);
            this.activeSnapshotId = response.data.active_id || "";
            this.backToOverview();
            await this.loadSnapshots();
            await this.loadTables();
            this.$message.success(this.$t("msg.delete_snapshot_success"));
          } catch (e) {
            this.$message.error(this.$t("msg.delete_snapshot_fail", { msg: e.response?.data?.error || e.message }));
          }
        })
        .catch(() => {});
    },

    async loadTables() {
      try {
        const res = await apiClient.get("/api/tables");
        this.tables = res.data.tables;
        this.syncTablePagination();
      } catch (e) {
        this.$message.error(this.$t("msg.load_tables_fail", { msg: e.message }));
      }
    },

    async addTable() {
      try {
        const tableResult = await this.$prompt(
          this.$t("overview.add_table_name_prompt"),
          this.$t("overview.add_table_title"),
          {
            confirmButtonText: this.$t("overview.next"),
            cancelButtonText: this.$t("dialog.cancel"),
            inputPlaceholder: this.$t("overview.add_table_name_placeholder"),
            inputValidator: (value) => Boolean(value?.trim()) || this.$t("overview.table_name_required"),
          },
        );
        const columnsResult = await this.$prompt(
          this.$t("overview.add_columns_prompt"),
          this.$t("overview.add_table_title"),
          {
            confirmButtonText: this.$t("dialog.add"),
            cancelButtonText: this.$t("dialog.cancel"),
            inputPlaceholder: this.$t("overview.add_columns_placeholder"),
            inputValidator: (value) =>
              Boolean(value?.split(/[,，\n]/).some((column) => column.trim())) || this.$t("overview.columns_required"),
          },
        );
        const columns = [...new Set(columnsResult.value.split(/[,，\n]/).map((column) => column.trim()).filter(Boolean))];
        const response = await apiClient.post("/api/tables", {
          table_name: tableResult.value.trim(),
          columns,
        });
        await this.loadTables();
        this.$message.success(this.$t("msg.add_table_success"));
        this.enterTable(response.data.table);
      } catch (e) {
        if (e === "cancel" || e === "close") return;
        this.$message.error(this.$t("msg.add_table_fail", { msg: e.response?.data?.error || e.message }));
      }
    },

    deleteTable(table) {
      this.$confirm(
        this.$t("confirm.delete_table_content", { name: table.table_name, count: table.count }),
        this.$t("confirm.delete_table_title"),
        {
          confirmButtonText: this.$t("confirm.btn_confirm"),
          cancelButtonText: this.$t("confirm.btn_cancel"),
          type: "warning",
        },
      )
        .then(async () => {
          try {
            await apiClient.post("/api/tables/delete", { table_name: table.table_name });
            await this.loadTables();
            this.$message.success(this.$t("msg.delete_table_success"));
          } catch (e) {
            this.$message.error(this.$t("msg.delete_table_fail", { msg: e.response?.data?.error || e.message }));
          }
        })
        .catch(() => {});
    },

    enterTable(row) {
      this.selectedTable = row.table_name;
      this.currentColumns = row.columns || [];
      this.pagination.page = 1;
      this.sort = { prop: null, order: null };
      this.columnFilters = {};
      this.clearSelectedRows();
      this.sidebarCollapsed = false;
      this.loadConfigs();
    },

    backToOverview() {
      this.selectedTable = "";
      this.currentColumns = [];
      this.configs = [];
      this.clearSelectedRows();
      this.columnFilters = {};
      this.sidebarCollapsed = false;
    },

    handleSortChange({ prop, order }) {
      this.sort.prop = prop ? prop.replace("config_data.", "") : null;
      this.sort.order = order === "ascending" ? "asc" : order === "descending" ? "desc" : null;
      this.pagination.page = 1;
      this.loadConfigs();
    },

    handleFilterChange(filters) {
      this.columnFilters = filters;
      this.pagination.page = 1;
      this.clearSelectedRows();
      this.loadConfigs();
    },

    async loadConfigs() {
      if (!this.selectedTable) return;
      this.loading = true;
      try {
        const params = {
          page: this.pagination.page,
          page_size: this.pagination.pageSize,
          table_name: this.selectedTable,
        };
        if (this.sort.prop) {
          params.sort_by = this.sort.prop;
          params.sort_order = this.sort.order;
        }
        if (Object.keys(this.columnFilters).length) params.filters = JSON.stringify(this.columnFilters);
        const res = await apiClient.get("/api/configs", { params });
        this.configs = res.data.configs;
        this.pagination.total = res.data.total;
        this.pagination.page = res.data.page;
        if (this.configs.length > 0) {
          const keys = Object.keys(this.configs[0].config_data);
          if (keys.length !== this.currentColumns.length) {
            this.currentColumns = keys;
          }
        }
      } catch (e) {
        this.$message.error(this.$t("msg.load_configs_fail", { msg: e.message }));
      } finally {
        this.loading = false;
      }
    },

    handleUploadStart() {
      this.uploading = true;
    },
    handleUploadSuccess(response) {
      this.uploading = false;
      this.$message.success(response.message);
      this.loadSnapshots();
      this.backToOverview();
      this.loadTables();
    },
    handleUploadError(error) {
      this.uploading = false;
      const msg = error?.message || (typeof error === "string" ? error : null) || this.$t("msg.upload_fail");
      this.$message.error(msg);
    },

    handleSizeChange(size) {
      this.pagination.pageSize = size;
      this.pagination.page = 1;
      this.loadConfigs();
    },
    handlePageChange(page) {
      this.pagination.page = page;
      this.loadConfigs();
    },

    async batchDelete() {
      if (!this.selectedRows.length) return;
      const count = this.selectedRows.length;
      this.$confirm(this.$t("confirm.batch_delete_content", { count }), this.$t("confirm.batch_delete_title"), {
        confirmButtonText: this.$t("confirm.btn_confirm"),
        cancelButtonText: this.$t("confirm.btn_cancel"),
        type: "warning",
      })
        .then(async () => {
          try {
            const ids = this.selectedRows.map((r) => r.id);
            await apiClient.post("/api/configs/batch-delete", { table_name: this.selectedTable, ids });
            this.$message.success(this.$t("msg.batch_delete_success", { count: ids.length }));
            this.clearSelectedRows();
            this.loadConfigs();
            this.loadTables();
          } catch (e) {
            this.$message.error(this.$t("msg.batch_delete_fail", { msg: e.response?.data?.error || e.message }));
          }
        })
        .catch(() => {});
    },

    async downloadExport(format, payload, successCount) {
      try {
        const res = await apiClient.post("/api/export", { format, ...payload }, { responseType: "blob" });
        const disposition = res.headers["content-disposition"] || "";
        const encodedName = disposition.match(/filename\*=UTF-8''([^;]+)/i)?.[1];
        const plainName = disposition.match(/filename="?([^";]+)"?/i)?.[1];
        const filename = encodedName ? decodeURIComponent(encodedName) : plainName || `export.${format}`;
        const url = window.URL.createObjectURL(res.data);
        const link = document.createElement("a");
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);
        const count = Number(res.headers["x-export-count"]) || successCount;
        this.$message.success(this.$t("msg.export_success", { count }));
        return true;
      } catch (e) {
        let msg = e.response?.data?.error || e.message;
        if (e.response?.data instanceof Blob) {
          try {
            const error = JSON.parse(await e.response.data.text());
            msg = error.error || msg;
          } catch (_) {
            // Keep the transport error when the response is not JSON.
          }
        }
        this.$message.error(this.$t("msg.export_fail", { msg }));
        return false;
      }
    },

    batchExport(format) {
      if (!this.selectedRows.length) return;
      const ids = this.selectedRows.map((row) => row.id);
      this.pendingExport = {
        format,
        scope: "selected",
        count: ids.length,
        payload: { table_name: this.selectedTable, ids },
        rows: [...this.selectedRows],
        columns: [...this.currentColumns],
        tables: [],
      };
      this.exportPreviewVisible = true;
    },

    exportAll(format) {
      const count = this.tables.reduce((total, table) => total + table.count, 0);
      this.pendingExport = {
        format,
        scope: "all",
        count,
        payload: {},
        rows: [],
        columns: [],
        tables: [...this.tables],
      };
      this.exportPreviewVisible = true;
    },

    async confirmExport() {
      if (!this.pendingExport || this.exporting) return;
      this.exporting = true;
      try {
        const success = await this.downloadExport(
          this.pendingExport.format,
          this.pendingExport.payload,
          this.pendingExport.count,
        );
        if (success) {
          this.exportPreviewVisible = false;
          this.pendingExport = null;
        }
      } finally {
        this.exporting = false;
      }
    },

    showAddRowDialog() {
      this.isNewRow = true;
      this.editForm = {};
      this.currentColumns.forEach((col) => {
        this.editForm[col] = "";
      });
      this.editDialogVisible = true;
    },

    handleEdit(row) {
      this.isNewRow = false;
      this.editForm = { ...row.config_data, _id: row.id };
      this.editDialogVisible = true;
    },

    async saveEdit() {
      try {
        const configData = {};
        this.currentColumns.forEach((col) => {
          configData[col] = this.editForm[col] || "";
        });
        if (this.isNewRow) {
          await apiClient.post("/api/configs", { table_name: this.selectedTable, config_data: configData });
          this.$message.success(this.$t("msg.add_success"));
        } else {
          await apiClient.put(`/api/configs/${this.editForm._id}`, {
            table_name: this.selectedTable,
            config_data: configData,
          });
          this.$message.success(this.$t("msg.save_success"));
        }
        this.editDialogVisible = false;
        this.loadConfigs();
        this.loadTables();
      } catch (e) {
        this.$message.error(this.$t("msg.save_fail", { msg: e.message }));
      }
    },

    handleDelete(row) {
      this.$confirm(this.$t("confirm.delete_content"), this.$t("confirm.delete_title"), {
        confirmButtonText: this.$t("confirm.btn_confirm"),
        cancelButtonText: this.$t("confirm.btn_cancel"),
        type: "warning",
      })
        .then(async () => {
          try {
            await apiClient.delete(`/api/configs/${row.id}`, { params: { table_name: this.selectedTable } });
            this.$message.success(this.$t("msg.delete_success"));
            this.loadConfigs();
          } catch (e) {
            this.$message.error(this.$t("msg.delete_fail", { msg: e.message }));
          }
        })
        .catch(() => {});
    },
  },
};
</script>
