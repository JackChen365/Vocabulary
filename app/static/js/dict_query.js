var last_selection=""
function mouse_listener(event) {
    if (event.target.closest("#query_div")) return;
    let selectionObj = window.getSelection();
    let selectedText = selectionObj.toString();
    let exp = new RegExp("^[a-zA-Z]*$");
    if($.trim(selectedText)&&selectedText!=last_selection&&exp.test($.trim(selectedText))){
        //查询单词信息
        window.location.href = '?word='+selectedText;
        last_selection = selectedText
    }
}

function set_drag_sort(){
    let dict_items=$(".dict-item-class")
      var sort_before=new Array()
      for(let i=0;i<dict_items.length;i++) {
          sort_before.push(dict_items[i].id)
      }
    $(".slides").sortable({
        placeholder: 'slide-placeholder',
        axis: "y",
        revert: 150,
        start: function(e, ui){
            placeholderHeight = ui.item.outerHeight();
            ui.placeholder.height(placeholderHeight);
            $('<div class="slide-placeholder-animator" data-height="' + placeholderHeight + '"></div>').insertAfter(ui.placeholder);
        },
        change: function(event, ui) {
            ui.placeholder.stop().height(0).animate({
                height: ui.item.outerHeight()
            }, 300);
            placeholderAnimatorHeight = parseInt($(".slide-placeholder-animator").attr("data-height"));
            $(".slide-placeholder-animator").stop().height(placeholderAnimatorHeight).animate({
                height: 0
            }, 300, function() {
                $(this).remove();
                placeholderHeight = ui.item.outerHeight();
                $('<div class="slide-placeholder-animator" data-height="' + placeholderHeight + '"></div>').insertAfter(ui.placeholder);
            });
        },
        stop: function(e, ui) {
            $(".slide-placeholder-animator").remove();
             let dict_items=$(".dict-item-class")
              let position_items=new Array()
              for(let i=0;i<dict_items.length;i++) {
                  position_items.push(dict_items[i].id)
              }
              if(JSON.stringify(sort_before)!=JSON.stringify(position_items)){
                sort_dict_list(position_items)
              }
        },
    });
}

function copyStringToClipboard (str) {
   let el = document.createElement('textarea');
   el.value = str;
   el.setAttribute('readonly', '');
   el.style = {position: 'absolute', left: '-9999px'};
   document.body.appendChild(el);
   el.select();
   document.execCommand('copy');
   document.body.removeChild(el);
}

function query_list_selected(){
    $('.query-list .query-item-class').click(function(){
        $(this).parent().find('.query-item-class').removeClass('selected');
        $(this).addClass('selected');
        copyStringToClipboard($(this)[0].innerText)
    });
}

function query_dict_selected(){
    $('.dict-list .dict-item-class').click(function(){
        $(this).parent().find('.dict-item-class').removeClass('selected');
        $(this).addClass('selected');
        let index=$(".dict-item-class").index($(this)[0])
        let item_div=$(".dict-content-item")[index]
        let offsetTop = item_div.offsetTop - item_div.scrollTop + item_div.clientTop
        $('html, body').animate({scrollTop: offsetTop - 120 }, 'slow');
    });
}

function tag_group_selected() {
    $(".tag-group .tag-item").mouseover((ev)=>{
         $(ev.target).addClass('selected');
    });
    $(".tag-group .tag-item").mouseout((ev)=>{
         $(ev.target).removeClass("selected");
    });
    $('.tag-group .tag-item').click((ev)=>{
        $(ev.target).parent().find('.tag-item').removeClass('clicked');
        $(ev.target).addClass('clicked');
        let url = new URL(window.location.href);
        let word = url.searchParams.get("word");
        if(null!=word){
            //提交数据
            set_word_tag(word,ev.target.id)
        }
    });
}

function dict_title_click_event() {
    $(".dict_content-title").click(function(){
        let content_div = $("#"+$(this)[0].id+"-content")
        if(content_div.css('display') == 'none'){
           content_div.slideDown('slow');
        } else {
           content_div.slideUp('slow');
        }
    })
}

function sort_dict_list(position_items) {
        console.info("开始重新排序！");
        let form_data = new FormData();
          form_data.append("position",JSON.stringify(position_items))
        $.ajax({
            type: 'POST',
            url: $("input[name=dict-sort-item]").val(),
            contentType:false,
            processData:false,
            cache: false,
            dataType: 'text',
            data:form_data,
            beforeSend: function (xhr, setting) {
                xhr.setRequestHeader("X-CSRFToken", $("input[name=csrfmiddlewaretoken]").val())
            },
            success: function(data){
                console.info("排序成功:")
            },
            error: function(e){
                console.info("排序失败:"+e)
            }
        })
}

function set_word_tag(word, tag) {
        console.info(`设置单词:${word}标签-${tag}！`);
        let form_data = new FormData();
        form_data.append("word",word)
        form_data.append("tag",tag)
        $.ajax({
            type: 'POST',
            url: $("input[name=query-translate-tag]").val(),
            contentType:false,
            processData:false,
            cache: false,
            dataType: 'json',
            data:form_data,
            beforeSend: function (xhr, setting) {
                xhr.setRequestHeader("X-CSRFToken",$("input[name=csrfmiddlewaretoken]").val())
            },
            success: function(data){
                console.info(data.message)
            },
            error: function(e){
                console.info(data.message)
            }
        })
}

function session_list_selected(select_id){
    $.each($('.query-session-list .query-session-class'),(index,ele)=>$(ele).removeClass('selected'));
    $(`.query-session-list #${select_id}`).addClass('selected');
}

function set_study_session_file(file_id){
    console.info("request set study session!")
    let form_data = new FormData();
    form_data.append("file_id",file_id)
    $.ajax({
        type: 'POST',
        url: $("input[name=study-session-file]").val(),
        contentType:false,
        processData:false,
        cache: false,
        data:form_data,
        dataType: 'json',
        xhrFields: { withCredentials: true },
        success: function(data){
            console.info("request sueess!"+data)
            if(!data.is_valid){
                console.info("request failed:"+data.message);
            } else {
                console.info("request sueess!")
                //设置选中事件
                session_list_selected(data.data)
            }
        },
        error: function(e){
            console.info("request failed:"+e)
        }
    })
}


function delete_word_history(word,div_id){
    let form_data = new FormData();
    form_data.append("word",word)
        $.ajax({
            type: 'POST',
            url:$("input[name=user-delete-query]").val(),
            contentType:false,
            processData:false,
            cache: false,
            dataType: 'text',
            data:form_data,
            beforeSend: function (xhr, setting) {
                xhr.setRequestHeader("X-CSRFToken", $("input[name=csrfmiddlewaretoken]").val())
            },
            success: function(data){
                $("#"+div_id).remove();
                let count_item=$("#query-history-count")
                let count=parseInt(count_item.text())
                count_item[0].innerText=count-1
                console.info("delete success:")
            },
            error: function(e){
                console.info("delete failed:"+e)
            }
        })
}

function onWindowPaste( e ){
    e.preventDefault();
    let pastedText = undefined;
    if( window.clipboardData && window.clipboardData.getData ){
        pastedText = window.clipboardData.getData('Text');
    } else if( e.clipboardData && e.clipboardData.getData ){
        pastedText = e.clipboardData.getData('text/plain');
    }
    let exp = new RegExp("^[a-zA-Z]*$");
    if(exp.test($.trim(pastedText))){
        window.location.href = '?word='+pastedText;
    }
}

window.onload=function(){
    let eleItems = document.getElementsByTagName("a");
    const eleArray = Array.prototype.slice.call(eleItems)
    const audioArray=eleArray.filter(function (element) {
        return element.href.endsWith("mp3")||element.href.endsWith("wav")
    })
    for(let i=0;i<audioArray.length;i++){
        let link_tag=audioArray[i]
        const href=link_tag.href
        link_tag.href="javascript:void(0)"
        let playAudioItem
        link_tag.addEventListener("click",function () {
            if(playAudioItem){
                playAudioItem.pause();
                playAudioItem.currentTime = 0;
            }
            let audioItem=new Audio(href)
            audioItem.play()
            playAudioItem=audioItem
        })
    }
    //select text event
    let query_content=document.getElementById("query-content")
    query_content.addEventListener('mouseup',mouse_listener , true);
    query_content.addEventListener('dblclick', mouse_listener, true);
    // drag set event
    dict_title_click_event()
    query_list_selected()
    query_dict_selected()
    tag_group_selected()
    set_drag_sort()
    //set window paste
    document.onpaste = onWindowPaste;
    window.addEventListener("focus",()=>document.getElementById("search_word").focus())
}
