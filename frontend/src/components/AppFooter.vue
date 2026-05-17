<template>
  <div ref="footerWrapper">
    <footer v-show="showFooter" class="vue-footer">
      <div class="footer-content">
        <span class="footer-license">
          <svg viewBox="0 0 24 24" width="14" height="14" fill="#999" style="vertical-align: -2px; margin-right: 4px;">
            <path d="M12 2L2 7v5c0 5.25 3.86 10.14 10 11 6.14-.86 10-5.75 10-11V7l-10-5z"/>
          </svg>
          MIT License
        </span>
        <span class="footer-sep">·</span>
        <span class="footer-copyright">
          &copy; {{ year }} <a href="https://github.com/wzklhk" target="_blank" class="copyright-link">wzklhk</a>. All rights reserved.
        </span>
      </div>
    </footer>
  </div>
</template>

<script>
export default {
  name: 'AppFooter',
  props: {
    showFooter: { type: Boolean, default: false }
  },
  computed: {
    year() { return new Date().getFullYear() }
  }
}
</script>

<style scoped>
.vue-footer {
  flex-shrink: 0;
  background: var(--footer-bg);
  border-top: 1px solid var(--header-border);
  padding: 14px 24px;
  text-align: center;
  transition: background 0.3s;
}
.footer-content {
  font-size: 12.5px; color: #888;
  display: flex; align-items: center; justify-content: center; gap: 10px;
}
.footer-license { display: inline-flex; align-items: center; color: #999; }
.footer-sep { color: #555; }
.footer-copyright { color: #888; }
.copyright-link { color: #aaa; text-decoration: none; transition: color 0.15s; }
.copyright-link:hover { color: #41b883; }

</style>
