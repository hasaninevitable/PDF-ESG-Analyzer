/**
 * Ultra Sharp PDF Viewer - Maximum Quality Rendering
 * Forces the highest possible rendering quality for crisp text
 */

class UltraSharpPDFViewer {
  constructor() {
    this.pdfDoc = null;
    this.pageViews = {};
    this.currentHighlightBox = null;
    this.pendingHighlight = null;
    
    // Ultra-high rendering settings
    this.RENDER_SCALE = 6.0; // Even higher than before
    this.MIN_DISPLAY_SCALE = 1.0;
    this.MAX_DISPLAY_SCALE = 2.5;
    
    this.initializeElements();
    this.parseURLParams();
    this.setupWorker();
  }

  initializeElements() {
    this.pageWrap = document.getElementById('page-wrap');
    this.loadingBox = document.getElementById('loading-box');
    this.highlightInfo = document.getElementById('highlight-info');
  }

  setupWorker() {
    pdfjsLib.GlobalWorkerOptions.workerSrc = 
      "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
  }

  parseURLParams() {
    const urlParams = new URLSearchParams(window.location.search);
    this.pdfFile = urlParams.get('file');
    const highlightParam = urlParams.get('highlight');
    
    console.log('PDF file:', this.pdfFile);
    
    if (highlightParam) {
      try {
        const parsed = JSON.parse(decodeURIComponent(highlightParam));
        if (parsed.page && parsed.coords) {
          this.pendingHighlight = {
            page: parsed.page,
            x0: parsed.coords.x0,
            y0: parsed.coords.y0,
            x1: parsed.coords.x1,
            y1: parsed.coords.y1
          };
          
          this.highlightInfo.style.display = 'block';
          document.getElementById('target-page').textContent = parsed.page;
        }
      } catch (e) {
        console.error('Failed to parse highlight data:', e);
      }
    }
  }

  async renderAllPages() {
    if (!this.pdfFile) {
      this.showError('No PDF file specified');
      return;
    }
    
    try {
      const pdfUrl = `/uploads/${this.pdfFile}`;
      console.log('Loading PDF from:', pdfUrl);
      
      this.pdfDoc = await pdfjsLib.getDocument(pdfUrl).promise;
      this.loadingBox.classList.add('hidden');
      console.log('PDF loaded:', this.pdfDoc.numPages, 'pages');
      
      for (let pageNum = 1; pageNum <= this.pdfDoc.numPages; pageNum++) {
        await this.renderUltraSharpPage(pageNum);
        
        if (this.pendingHighlight && this.pendingHighlight.page === pageNum) {
          setTimeout(() => this.applyHighlight(this.pendingHighlight), 500);
        }
      }
      
      console.log('All pages rendered at maximum quality');
      
    } catch (e) {
      this.showError(`Failed to load PDF: ${e.message}`);
      console.error('PDF loading error:', e);
    }
  }

  async renderUltraSharpPage(pageNum) {
    const page = await this.pdfDoc.getPage(pageNum);
    const baseViewport = page.getViewport({ scale: 1.0 });
    
    // Calculate display scale
    const maxWidth = window.innerWidth * 0.9;
    const maxHeight = window.innerHeight * 0.8;
    const scaleX = maxWidth / baseViewport.width;
    const scaleY = maxHeight / baseViewport.height;
    const displayScale = Math.min(
      Math.max(Math.min(scaleX, scaleY), this.MIN_DISPLAY_SCALE), 
      this.MAX_DISPLAY_SCALE
    );
    
    const displayViewport = page.getViewport({ scale: displayScale });
    const renderViewport = page.getViewport({ scale: this.RENDER_SCALE });
    
    console.log(`Page ${pageNum}: Display ${displayScale.toFixed(2)}x, Render ${this.RENDER_SCALE}x`);
    
    // Create page container
    const pageDiv = this.createPageContainer(pageNum, displayViewport);
    
    // Create ultra-sharp canvas
    const canvas = this.createMaxQualityCanvas(renderViewport, displayViewport);
    const context = canvas.getContext('2d');
    
    // CRITICAL: Disable ALL forms of smoothing
    this.disableAllSmoothing(context);
    
    pageDiv.appendChild(canvas);
    
    // Render at maximum resolution
    const renderContext = {
      canvasContext: context,
      viewport: renderViewport,
      intent: 'display',
      renderInteractiveForms: false,
      optionalContentConfigPromise: null
    };
    
    await page.render(renderContext).promise;
    
    // Store page info
    this.pageViews[pageNum] = { 
      pageDiv, 
      viewport: displayViewport,
      scale: displayScale,
      isLandscape: baseViewport.width > baseViewport.height
    };
    
    console.log(`Page ${pageNum}: Canvas ${canvas.width}x${canvas.height} -> Display ${canvas.style.width}x${canvas.style.height}`);
  }

  createPageContainer(pageNum, viewport) {
    const pageDiv = document.createElement('div');
    pageDiv.classList.add('page');
    
    if (viewport.width > viewport.height) {
      pageDiv.classList.add('landscape');
    }
    
    pageDiv.style.width = viewport.width + 'px';
    pageDiv.style.height = viewport.height + 'px';
    pageDiv.setAttribute('data-page', pageNum);
    
    // Add quality indicator
    const qualityInfo = document.createElement('div');
    qualityInfo.className = 'debug-info';
    qualityInfo.textContent = `Page ${pageNum} | ${this.RENDER_SCALE}x Quality`;
    qualityInfo.style.background = 'rgba(0,128,0,0.8)'; // Green for high quality
    pageDiv.appendChild(qualityInfo);
    
    this.pageWrap.appendChild(pageDiv);
    return pageDiv;
  }

  createMaxQualityCanvas(renderViewport, displayViewport) {
    const canvas = document.createElement('canvas');
    
    // Set canvas to ultra-high resolution
    canvas.width = renderViewport.width;
    canvas.height = renderViewport.height;
    
    // Display at appropriate size
    canvas.style.width = displayViewport.width + 'px';
    canvas.style.height = displayViewport.height + 'px';
    
    // Force sharp rendering via CSS
    canvas.style.imageRendering = 'pixelated';
    canvas.style.imageRendering = '-moz-crisp-edges';
    canvas.style.imageRendering = '-webkit-crisp-edges';
    canvas.style.imageRendering = 'crisp-edges';
    
    return canvas;
  }

  disableAllSmoothing(context) {
    // Disable every possible smoothing setting
    context.imageSmoothingEnabled = false;
    
    // Webkit
    if (context.webkitImageSmoothingEnabled !== undefined) {
      context.webkitImageSmoothingEnabled = false;
    }
    
    // Mozilla
    if (context.mozImageSmoothingEnabled !== undefined) {
      context.mozImageSmoothingEnabled = false;
    }
    
    // Microsoft
    if (context.msImageSmoothingEnabled !== undefined) {
      context.msImageSmoothingEnabled = false;
    }
    
    // Opera
    if (context.oImageSmoothingEnabled !== undefined) {
      context.oImageSmoothingEnabled = false;
    }
    
    console.log('All smoothing disabled for maximum sharpness');
  }

  applyHighlight(highlightData) {
    const { page, x0, y0, x1, y1 } = highlightData;
    
    if (!this.pageViews[page]) {
      console.error(`Page ${page} not found`);
      return;
    }
    
    const { pageDiv, viewport } = this.pageViews[page];
    
    // Clear previous highlights
    this.clearHighlights(pageDiv);

    try {
      // Use PDF.js transformation matrix
      const pageHeightPts = viewport.height / viewport.scale;
      const transform = viewport.transform;
      
      const A_pdf = [x0, pageHeightPts - y0];
      const B_pdf = [x1, pageHeightPts - y1];
      const A_vp = pdfjsLib.Util.applyTransform(A_pdf, transform);
      const B_vp = pdfjsLib.Util.applyTransform(B_pdf, transform);
      
      const left = Math.min(A_vp[0], B_vp[0]);
      const top = Math.min(A_vp[1], B_vp[1]);
      const width = Math.abs(B_vp[0] - A_vp[0]);
      const height = Math.abs(B_vp[1] - A_vp[1]);

      console.log('Highlight at:', { left, top, width, height });

      const highlightBox = this.createHighlight(left, top, width, height);
      pageDiv.appendChild(highlightBox);
      this.currentHighlightBox = highlightBox;

      setTimeout(() => {
        highlightBox.scrollIntoView({ 
          behavior: 'smooth', 
          block: 'center',
          inline: 'center'
        });
      }, 1000);
      
    } catch (error) {
      console.error('Error applying highlight:', error);
    }
  }

  createHighlight(left, top, width, height) {
    const highlightBox = document.createElement('div');
    highlightBox.className = 'highlight-box';
    highlightBox.style.left = left + 'px';
    highlightBox.style.top = top + 'px';
    highlightBox.style.width = width + 'px';
    highlightBox.style.height = height + 'px';
    return highlightBox;
  }

  clearHighlights(pageDiv) {
    if (this.currentHighlightBox) {
      this.currentHighlightBox.remove();
      this.currentHighlightBox = null;
    }
  }

  showError(message) {
    this.loadingBox.innerHTML = `<div class="error-box">${message}</div>`;
  }

  setupEventListeners() {
    window.addEventListener('message', event => {
      const data = event.data;
      if (data && data.page && data.x0 !== undefined) {
        this.applyHighlight(data);
      }
    });
  }

  async init() {
    this.setupEventListeners();
    await this.renderAllPages();
  }
}

// Initialize when DOM ready
document.addEventListener('DOMContentLoaded', () => {
  console.log('Initializing Ultra Sharp PDF Viewer...');
  const viewer = new UltraSharpPDFViewer();
  viewer.init().catch(console.error);
});