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
        :tables="pagedTables"
        :table-pagination="tablePagination"
        :columns="currentColumns"
        :total-rows="pagination.total"
        :collapsed="sidebarCollapsed"
        @toggle-sidebar="sidebarCollapsed = !sidebarCollapsed"
        @select-table="enterTable"
        @table-page-change="handleTablePageChange"
      />

      <el-main class="vue-main">
        <TableOverview
          v-show="!selectedTable"
          v-model="tableSearch"
          :tables="pagedTables"
          :can-export="tables.length > 0"
          :pagination="tablePagination"
          @enter-table="enterTable"
          @refresh="loadTables"
          @export-all="exportAll"
          @sort="handleOverviewSort"
          @page-change="handleTablePageChange"
          @size-change="handleTableSizeChange"
        />

        <TableDetail
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
  </div>
</template>

<script>
import VueHeader from "../../components/VueHeader.vue";
import Sidebar from "../../components/Sidebar.vue";
import TableOverview from "../../components/TableOverview.vue";
import TableDetail from "../../components/TableDetail.vue";
import EditDialog from "../../components/EditDialog.vue";
import CompareDialog from "../../components/CompareDialog.vue";
import apiClient from "../../api/client";

export default {
  name: "MmlQueryView",
  components: { VueHeader, Sidebar, TableOverview, TableDetail, EditDialog, CompareDialog },
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

    async loadSnapshots() {
      try {
        const res = await apiClient.get("/api/snapshots");
        this.snapshots = res.data.snapshots;
        this.activeSnapshotId = res.data.active_id || "";
      } catch (e) {
        this.$message.error(this.$t("msg.load_snapshots_fail", { msg: e.message }));
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

    enterTable(row) {
      this.selectedTable = row.table_name;
      this.currentColumns = row.columns || [];
      this.pagination.page = 1;
      this.sort = { prop: null, order: null };
      this.columnFilters = {};
      this.selectedRows = [];
      this.sidebarCollapsed = false;
      this.loadConfigs();
    },

    backToOverview() {
      this.selectedTable = "";
      this.currentColumns = [];
      this.configs = [];
      this.selectedRows = [];
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
      this.selectedRows = [];
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
            this.selectedRows = [];
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
      }
    },

    async batchExport(format) {
      if (!this.selectedRows.length) return;
      const ids = this.selectedRows.map((row) => row.id);
      await this.downloadExport(format, { table_name: this.selectedTable, ids }, ids.length);
    },

    async exportAll(format) {
      await this.downloadExport(
        format,
        {},
        this.tables.reduce((total, table) => total + table.count, 0),
      );
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
