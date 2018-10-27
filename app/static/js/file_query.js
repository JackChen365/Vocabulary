//查询单词信息
function query_word(word) {
        console.info("查询单词！"+word)
        $.ajax({
            type: 'GET',
            url: $("input[name=query-box]").val()+'?word='+word,
            contentType:false,
            processData:false,
            cache: false,
            dataType: 'text',
            beforeSend: function (xhr, setting) {
                xhr.setRequestHeader("X-CSRFToken", $("input[name=csrfmiddlewaretoken]").val())
            },
            success: function(data){
                console.info("请求成功:"+word)
                $("#query_div").prepend(data)
            },
            error: function(e){
                console.info("请求失败:"+e)
            }
        })
}
var last_selection=""
var is_popup_open=false
document.addEventListener('click',function(event){
    if (event.target.closest("#query_div")) return;
    if(!is_popup_open){
        let query_div=document.getElementById("query_div")
        query_div.style.display="none"
        query_div.innerHTML=""
    }
    is_popup_open=false
});
function mouse_listener(event) {
    if (event.target.closest("#query_div")) return;
    let selectionObj = window.getSelection();
    let selectedText = selectionObj.toString();
    if($.trim(selectedText)&&selectedText!=last_selection){
        let query_div=document.getElementById("query_div")
        let col_md_9=$(".col-md-9")
        let divOffsetLeft=col_md_9.offset() ?col_md_9.offset().left:0;
        let divOffsetTop=col_md_9.offset() ?col_md_9.offset().top:0;
        let div_width=$('#query_div').width();
        let div_height=$('#query_div').height();
        let left_offset=10
        let top_offset=10
        let scroll_top=$(document).scrollTop()
        let mousePosition = {
            x : event.clientX+left_offset-divOffsetLeft,
            y : event.clientY+scroll_top+top_offset-divOffsetTop
        };
        if(event.clientX+div_width+divOffsetLeft>window.innerWidth){
            mousePosition.x=event.clientX-div_width-left_offset*2
        }
        if(event.clientY+div_height>window.innerHeight){
            mousePosition.y=event.clientY+scroll_top-divOffsetTop-div_height-top_offset*2
        }
        console.info((event.clientY+div_height)+" "+window.innerHeight)
        query_div.style.left = (mousePosition.x) + 'px';
        query_div.style.top  = (mousePosition.y) + 'px';
        query_div.style.display="block"
        is_popup_open=true
        //查询单词信息
        query_word(selectedText)
    }
    last_selection = selectedText
}

function play_uk(sound){
    new Audio(sound).play();
}
function play_us(sound){
    new Audio(sound).play();
}
function show_hide(word){
    let desc_div=document.getElementById(word+"_desc")
    let link_link=document.getElementById(word+"_link")
    if(desc_div.style.display=="none"){
        desc_div.style.display = "block";
    }else{
        desc_div.style.display = "none";
    }
    link_link.style.display="none"
}
window.onload=function(){
    let sentence_list=document.getElementById("sentence_list")
    sentence_list.addEventListener('mouseup',mouse_listener , true);
    sentence_list.addEventListener('dblclick', mouse_listener, true);
}
