// 全局变量
let subtitles = [];
let videoPlayer = null;
let currentActiveSubtitle = null;

// DOM 元素
const subtitleList = document.getElementById('subtitleList');
const subtitleCount = document.getElementById('subtitleCount');
const currentTimeDisplay = document.getElementById('currentTimeDisplay');
const currentSpeaker = document.getElementById('currentSpeaker');
const jsonFileInput = document.getElementById('jsonFile');
const videoFileInput = document.getElementById('videoFile');

// 初始化
document.addEventListener('DOMContentLoaded', function() {
    videoPlayer = document.getElementById('videoPlayer');
    
    // 尝试加载默认的字幕文件
    loadDefaultSubtitles();
    
    // 设置事件监听器
    setupEventListeners();
});

// 设置事件监听器
function setupEventListeners() {
    // 视频时间更新事件
    videoPlayer.addEventListener('timeupdate', updateCurrentTime);
    
    // 文件选择事件
    jsonFileInput.addEventListener('change', handleJsonFileSelect);
    videoFileInput.addEventListener('change', handleVideoFileSelect);
    
    // 视频加载事件
    videoPlayer.addEventListener('loadedmetadata', function() {
        console.log('视频加载完成');
    });
    
    videoPlayer.addEventListener('error', function(e) {
        console.error('视频加载错误:', e);
    });
}

// 尝试加载默认字幕文件
async function loadDefaultSubtitles() {
    try {
        // 尝试加载 SamT_transcript.json
        const response = await fetch('SamT_transcript.json');
        if (response.ok) {
            const data = await response.json();
            loadSubtitles(data);
            console.log('成功加载默认字幕文件: SamT_transcript.json');
        } else {
            throw new Error('默认文件不存在');
        }
    } catch (error) {
        console.log('未找到默认字幕文件，请手动选择');
        subtitleList.innerHTML = `
            <div class="loading">
                <p>未找到默认字幕文件</p>
                <p>请使用下方的文件选择器加载字幕文件</p>
            </div>
        `;
    }
}

// 处理JSON文件选择
function handleJsonFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            try {
                const data = JSON.parse(e.target.result);
                loadSubtitles(data);
                console.log('成功加载字幕文件:', file.name);
            } catch (error) {
                alert('字幕文件格式错误，请检查JSON格式');
                console.error('JSON解析错误:', error);
            }
        };
        reader.readAsText(file);
    }
}

// 处理视频文件选择
function handleVideoFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        const url = URL.createObjectURL(file);
        videoPlayer.src = url;
        console.log('成功加载视频文件:', file.name);
    }
}

// 加载字幕数据
function loadSubtitles(data) {
    subtitles = data;
    renderSubtitles();
    updateSubtitleStats();
}

// 渲染字幕列表
function renderSubtitles() {
    if (!subtitles || subtitles.length === 0) {
        subtitleList.innerHTML = '<div class="loading">没有字幕数据</div>';
        return;
    }
    
    const html = subtitles.map((subtitle, index) => {
        const speakerClass = subtitle.speaker === '自己' ? 'speaker-self' : 'speaker-other';
        const startTime = formatTime(subtitle.start);
        const endTime = formatTime(subtitle.end);
        
        return `
            <div class="subtitle-item" data-index="${index}" onclick="jumpToTime(${subtitle.start})">
                <div class="subtitle-time">
                    <span class="time-range">${startTime} - ${endTime}</span>
                    <span class="speaker-tag ${speakerClass}">${subtitle.speaker}</span>
                </div>
                <div class="subtitle-text">${subtitle.text}</div>
            </div>
        `;
    }).join('');
    
    subtitleList.innerHTML = html;
}

// 更新字幕统计信息
function updateSubtitleStats() {
    const selfCount = subtitles.filter(s => s.speaker === '自己').length;
    const otherCount = subtitles.filter(s => s.speaker === '对方').length;
    const totalDuration = subtitles.length > 0 ? Math.max(...subtitles.map(s => s.end)) : 0;
    
    subtitleCount.innerHTML = `
        总计 ${subtitles.length} 条字幕 | 
        自己: ${selfCount} 条 | 
        对方: ${otherCount} 条 | 
        时长: ${formatTime(totalDuration)}
    `;
}

// 跳转到指定时间
function jumpToTime(time) {
    if (videoPlayer) {
        videoPlayer.currentTime = time;
        videoPlayer.play();
        console.log(`跳转到时间: ${formatTime(time)}`);
    }
}

// 更新当前时间显示和高亮字幕
function updateCurrentTime() {
    const currentTime = videoPlayer.currentTime;
    currentTimeDisplay.textContent = formatTime(currentTime);
    
    // 找到当前时间对应的字幕
    const currentSubtitle = findCurrentSubtitle(currentTime);
    
    // 更新当前说话人
    if (currentSubtitle) {
        currentSpeaker.textContent = currentSubtitle.speaker;
        currentSpeaker.className = currentSubtitle.speaker === '自己' ? 'speaker-self' : 'speaker-other';
    } else {
        currentSpeaker.textContent = '-';
        currentSpeaker.className = '';
    }
    
    // 高亮当前字幕
    highlightCurrentSubtitle(currentSubtitle);
}

// 查找当前时间对应的字幕
function findCurrentSubtitle(currentTime) {
    return subtitles.find(subtitle => 
        currentTime >= subtitle.start && currentTime <= subtitle.end
    );
}

// 高亮当前字幕
function highlightCurrentSubtitle(currentSubtitle) {
    // 移除之前的高亮
    if (currentActiveSubtitle) {
        currentActiveSubtitle.classList.remove('active');
    }
    
    if (currentSubtitle) {
        const index = subtitles.indexOf(currentSubtitle);
        const subtitleElement = document.querySelector(`[data-index="${index}"]`);
        
        if (subtitleElement) {
            subtitleElement.classList.add('active');
            currentActiveSubtitle = subtitleElement;
            
            // 滚动到当前字幕
            subtitleElement.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        }
    } else {
        currentActiveSubtitle = null;
    }
}

// 格式化时间显示
function formatTime(seconds) {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
}

// 键盘快捷键
document.addEventListener('keydown', function(event) {
    if (!videoPlayer) return;
    
    switch(event.code) {
        case 'Space':
            event.preventDefault();
            if (videoPlayer.paused) {
                videoPlayer.play();
            } else {
                videoPlayer.pause();
            }
            break;
            
        case 'ArrowLeft':
            event.preventDefault();
            videoPlayer.currentTime = Math.max(0, videoPlayer.currentTime - 5);
            break;
            
        case 'ArrowRight':
            event.preventDefault();
            videoPlayer.currentTime = Math.min(videoPlayer.duration, videoPlayer.currentTime + 5);
            break;
            
        case 'ArrowUp':
            event.preventDefault();
            jumpToPreviousSubtitle();
            break;
            
        case 'ArrowDown':
            event.preventDefault();
            jumpToNextSubtitle();
            break;
    }
});

// 跳转到上一条字幕
function jumpToPreviousSubtitle() {
    const currentTime = videoPlayer.currentTime;
    const currentIndex = subtitles.findIndex(s => currentTime >= s.start && currentTime <= s.end);
    
    if (currentIndex > 0) {
        jumpToTime(subtitles[currentIndex - 1].start);
    } else if (currentIndex === -1 && subtitles.length > 0) {
        // 如果当前不在任何字幕时间段内，找到最近的前一条
        const previousSubtitle = subtitles.reverse().find(s => s.start < currentTime);
        if (previousSubtitle) {
            jumpToTime(previousSubtitle.start);
        }
        subtitles.reverse(); // 恢复原顺序
    }
}

// 跳转到下一条字幕
function jumpToNextSubtitle() {
    const currentTime = videoPlayer.currentTime;
    const currentIndex = subtitles.findIndex(s => currentTime >= s.start && currentTime <= s.end);
    
    if (currentIndex !== -1 && currentIndex < subtitles.length - 1) {
        jumpToTime(subtitles[currentIndex + 1].start);
    } else if (currentIndex === -1 && subtitles.length > 0) {
        // 如果当前不在任何字幕时间段内，找到最近的下一条
        const nextSubtitle = subtitles.find(s => s.start > currentTime);
        if (nextSubtitle) {
            jumpToTime(nextSubtitle.start);
        }
    }
}

// 快速加载JSON文件
function loadQuickJson(filename) {
    fetch(filename)
        .then(response => {
            if (!response.ok) {
                throw new Error(`无法加载文件: ${filename}`);
            }
            return response.json();
        })
        .then(data => {
            loadSubtitles(data);
            console.log(`快速加载字幕文件: ${filename}`);
        })
        .catch(error => {
            alert(`加载字幕文件失败: ${error.message}`);
            console.error('快速加载字幕失败:', error);
        });
}

// 快速加载视频文件
function loadQuickVideo(videoPath) {
    videoPlayer.src = videoPath;
    console.log(`快速加载视频文件: ${videoPath}`);
    
    // 监听视频加载事件
    videoPlayer.addEventListener('loadeddata', function() {
        console.log('视频加载成功');
    }, { once: true });
    
    videoPlayer.addEventListener('error', function(e) {
        console.error('视频加载失败:', e);
        alert('视频加载失败，请检查文件路径或使用文件选择器手动选择视频文件');
    }, { once: true });
}

// 调试信息
console.log('会议录制转录播放器已加载');
console.log('快捷键说明:');
console.log('- 空格键: 播放/暂停');
console.log('- 左右箭头: 快退/快进 5秒');
console.log('- 上下箭头: 上一条/下一条字幕'); 