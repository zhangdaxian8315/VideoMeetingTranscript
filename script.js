// 全局变量
let subtitles = [];
let videoPlayer = null;
let currentActiveSubtitle = null;
let isJumping = false; // 添加跳转状态标记

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
    
    // 尝试加载默认的视频文件
    loadDefaultVideo();
    
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
        console.log('✅ 视频元数据加载完成');
        console.log(`  时长: ${formatTime(videoPlayer.duration)}`);
        console.log(`  尺寸: ${videoPlayer.videoWidth}x${videoPlayer.videoHeight}`);
    });
    
    videoPlayer.addEventListener('loadeddata', function() {
        console.log('✅ 视频数据加载完成');
    });
    
    videoPlayer.addEventListener('canplay', function() {
        console.log('✅ 视频可以开始播放');
    });
    
    videoPlayer.addEventListener('canplaythrough', function() {
        console.log('✅ 视频可以流畅播放');
    });
    
    // Seek 相关事件
    videoPlayer.addEventListener('seeking', function() {
        console.log('🔍 Seeking 开始:', formatTime(videoPlayer.currentTime));
    });
    
    videoPlayer.addEventListener('seeked', function() {
        console.log('✅ Seeking 完成:', formatTime(videoPlayer.currentTime));
    });
    
    // 进度事件
    videoPlayer.addEventListener('progress', function() {
        if (videoPlayer.buffered.length > 0) {
            const bufferedEnd = videoPlayer.buffered.end(videoPlayer.buffered.length - 1);
            console.log(`📊 缓冲进度: ${formatTime(bufferedEnd)} / ${formatTime(videoPlayer.duration)}`);
        }
    });
    
    videoPlayer.addEventListener('error', function(e) {
        console.error('❌ 视频加载错误:', e);
        console.error('错误详情:', videoPlayer.error);
    });
    
    // 添加播放/暂停事件监听，清除跳转状态
    videoPlayer.addEventListener('play', function() {
        if (!isJumping) {
            console.log('▶️ 用户手动播放');
        }
    });
    
    videoPlayer.addEventListener('pause', function() {
        if (!isJumping) {
            console.log('⏸️ 用户手动暂停');
        }
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

// 尝试加载默认视频文件
async function loadDefaultVideo() {
    try {
        // 优先尝试加载混合音轨版的MP4视频
        const videoPath = 'recordings/SamT_2025-05-29_11-31-06_mixed.mp4';
        const response = await fetch(videoPath, { method: 'HEAD' });
        if (response.ok) {
            videoPlayer.src = videoPath;
            console.log('成功加载默认视频文件: SamT_2025-05-29_11-31-06_mixed.mp4 (混合音轨版)');
        } else {
            throw new Error('默认视频文件不存在');
        }
    } catch (error) {
        console.log('未找到混合音轨版视频，尝试优化版');
        // 尝试加载优化版MP4文件
        try {
            const fallbackPath = 'recordings/SamT_2025-05-29_11-31-06_web.mp4';
            const response = await fetch(fallbackPath, { method: 'HEAD' });
            if (response.ok) {
                videoPlayer.src = fallbackPath;
                console.log('加载备用视频文件: SamT_2025-05-29_11-31-06_web.mp4 (优化版)');
            } else {
                throw new Error('备用视频文件不存在');
            }
        } catch (fallbackError) {
            console.log('未找到优化版视频，尝试原版');
            // 最后尝试原版MKV文件
            try {
                const originalPath = 'recordings/SamT_2025-05-29 11-31-06.mkv';
                const response = await fetch(originalPath, { method: 'HEAD' });
                if (response.ok) {
                    videoPlayer.src = originalPath;
                    console.log('加载原版视频文件: SamT_2025-05-29 11-31-06.mkv');
                }
            } catch (originalError) {
                console.log('未找到任何默认视频文件');
            }
        }
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
            <div class="subtitle-item" data-index="${index}" data-start-time="${subtitle.start}">
                <div class="subtitle-time">
                    <span class="time-range">${startTime} - ${endTime}</span>
                    <span class="speaker-tag ${speakerClass}">${subtitle.speaker}</span>
                </div>
                <div class="subtitle-text">${subtitle.text}</div>
            </div>
        `;
    }).join('');
    
    subtitleList.innerHTML = html;
    
    // 重新绑定点击事件
    bindSubtitleClickEvents();
}

// 绑定字幕点击事件
function bindSubtitleClickEvents() {
    const subtitleItems = subtitleList.querySelectorAll('.subtitle-item');
    
    subtitleItems.forEach(item => {
        // 移除可能存在的旧事件监听器
        item.removeEventListener('click', handleSubtitleClick);
        // 添加新的事件监听器
        item.addEventListener('click', handleSubtitleClick);
    });
}

// 处理字幕点击事件
function handleSubtitleClick(event) {
    const startTime = parseFloat(event.currentTarget.dataset.startTime);
    console.log('用户点击字幕，跳转到时间:', startTime);
    jumpToTime(startTime);
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
    console.log('=== SEEK 调试开始 ===');
    console.log(`目标时间: ${formatTime(time)} (${time}秒)`);
    
    if (!videoPlayer) {
        console.error('视频播放器不存在');
        return;
    }
    
    // 详细的视频状态信息
    console.log('视频状态信息:');
    console.log(`  当前时间: ${formatTime(videoPlayer.currentTime)} (${videoPlayer.currentTime}秒)`);
    console.log(`  视频总时长: ${formatTime(videoPlayer.duration)} (${videoPlayer.duration}秒)`);
    console.log(`  就绪状态: ${videoPlayer.readyState} (0=无数据, 1=元数据, 2=当前帧, 3=未来帧, 4=足够数据)`);
    console.log(`  网络状态: ${videoPlayer.networkState} (0=空, 1=空闲, 2=加载中, 3=无源)`);
    console.log(`  是否暂停: ${videoPlayer.paused}`);
    console.log(`  是否结束: ${videoPlayer.ended}`);
    console.log(`  缓冲范围数量: ${videoPlayer.buffered.length}`);
    
    // 详细的缓冲信息
    if (videoPlayer.buffered.length > 0) {
        console.log('缓冲范围:');
        for (let i = 0; i < videoPlayer.buffered.length; i++) {
            const start = videoPlayer.buffered.start(i);
            const end = videoPlayer.buffered.end(i);
            console.log(`  范围${i}: ${formatTime(start)} - ${formatTime(end)} (${start.toFixed(2)} - ${end.toFixed(2)}秒)`);
        }
    } else {
        console.log('缓冲范围: 无');
    }
    
    // 详细的可搜索信息
    console.log(`可搜索范围数量: ${videoPlayer.seekable.length}`);
    if (videoPlayer.seekable.length > 0) {
        console.log('可搜索范围:');
        for (let i = 0; i < videoPlayer.seekable.length; i++) {
            const start = videoPlayer.seekable.start(i);
            const end = videoPlayer.seekable.end(i);
            console.log(`  范围${i}: ${formatTime(start)} - ${formatTime(end)} (${start.toFixed(2)} - ${end.toFixed(2)}秒)`);
        }
    } else {
        console.log('可搜索范围: 无');
    }
    
    // 设置跳转状态
    isJumping = true;
    
    // 记录用户是否在播放状态
    const wasPlaying = !videoPlayer.paused;
    console.log(`播放状态: ${wasPlaying ? '播放中' : '已暂停'}`);
    
    // 检查时间是否有效
    if (isNaN(time) || time < 0) {
        console.error('无效的时间值:', time);
        isJumping = false;
        return;
    }
    
    // 检查可搜索范围
    let adjustedTime = time;
    if (videoPlayer.seekable.length > 0) {
        const seekableEnd = videoPlayer.seekable.end(0);
        const seekableStart = videoPlayer.seekable.start(0);
        
        console.log(`目标时间检查: ${time} 是否在 [${seekableStart}, ${seekableEnd}] 范围内`);
        
        if (time > seekableEnd) {
            adjustedTime = Math.max(0, seekableEnd - 1);
            console.warn(`目标时间超出范围，调整为: ${formatTime(adjustedTime)} (${adjustedTime}秒)`);
        } else if (time < seekableStart) {
            adjustedTime = seekableStart;
            console.warn(`目标时间小于起始时间，调整为: ${formatTime(adjustedTime)} (${adjustedTime}秒)`);
        } else {
            console.log('目标时间在可搜索范围内');
        }
    } else {
        console.warn('没有可搜索范围，可能视频还在加载中');
        adjustedTime = Math.min(time, 5);
        console.log(`限制跳转到: ${formatTime(adjustedTime)} (${adjustedTime}秒)`);
    }
    
    // 执行跳转
    console.log(`准备执行 seek: ${videoPlayer.currentTime} -> ${adjustedTime}`);
    
    try {
        const beforeSeek = videoPlayer.currentTime;
        videoPlayer.currentTime = adjustedTime;
        const afterSeek = videoPlayer.currentTime;
        
        console.log(`Seek 执行结果:`);
        console.log(`  设置前: ${formatTime(beforeSeek)} (${beforeSeek.toFixed(3)}秒)`);
        console.log(`  设置值: ${formatTime(adjustedTime)} (${adjustedTime.toFixed(3)}秒)`);
        console.log(`  设置后: ${formatTime(afterSeek)} (${afterSeek.toFixed(3)}秒)`);
        console.log(`  是否成功: ${Math.abs(afterSeek - adjustedTime) < 1 ? '是' : '否'}`);
        
        // 短暂延迟后检查跳转结果并恢复播放状态
        setTimeout(() => {
            const finalTime = videoPlayer.currentTime;
            console.log(`延迟后检查:`);
            console.log(`  最终时间: ${formatTime(finalTime)} (${finalTime.toFixed(3)}秒)`);
            console.log(`  与目标差异: ${Math.abs(finalTime - adjustedTime).toFixed(3)}秒`);
            
            if (wasPlaying && Math.abs(finalTime - adjustedTime) <= 2) {
                console.log('恢复播放状态');
                videoPlayer.play();
            } else {
                console.log('不恢复播放状态');
            }
            
            // 清除跳转状态
            isJumping = false;
            console.log('=== SEEK 调试结束 ===');
        }, 200);
        
    } catch (error) {
        console.error('Seek 执行失败:', error);
        isJumping = false;
        console.log('=== SEEK 调试结束 (错误) ===');
    }
}

// 更新当前时间显示和高亮字幕
function updateCurrentTime() {
    const currentTime = videoPlayer.currentTime;
    currentTimeDisplay.textContent = formatTime(currentTime);
    
    // 在跳转过程中，减少不必要的字幕更新操作
    if (isJumping) {
        return;
    }
    
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
            
            // 滚动到当前字幕（只在非跳转状态下滚动，避免干扰用户操作）
            if (!isJumping) {
                subtitleElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            }
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
    }
});

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
console.log('- 点击字幕: 跳转到对应时间点'); 