var currentCid = 0; // 当前分类 id
var cur_page = 1; // 当前页
var total_page = 1;  // 总页数
var data_querying = false;   // 是否正在向后台获取数据

$(function () {
    //界面加载完成后请求article_list
    updateNewsData()
    //监听菜单的点击事件
    $('.menu li').click(function () {
        // 取到相应的被点击的li
        var clickCid = $(this).attr('data-cid');
        if (clickCid != currentCid) {
            // 记录当前分类id
            currentCid = clickCid;

            // 重置分页参数
            cur_page = 1;
            total_page = 1;
            updateNewsData()
        }
    });
    //页面滚动到最底下加载下一页的信息
    $(window).scroll(function () {

        // 浏览器窗口高度
        var showHeight = $(window).height();

        // 整个网页的高度
        var pageHeight = $(document).height();

        // 页面可以滚动的距离
        var canScrollHeight = pageHeight - showHeight;

        // 页面滚动了多少,这个是随着页面滚动实时变化的
        var nowScroll = $(document).scrollTop();

        if ((canScrollHeight - nowScroll) < 100) {
            //判断页数，去更新新闻数据
            if (!data_querying){  //如果当前没有在加载数据，开始加载数据
                data_querying = true;
                if (cur_page<total_page){
                    cur_page += 1;  //下一页
                    updateNewsData();
                    data_querying = false;
                }
            }
        }
    })
});

function updateNewsData() {
    //更新新闻数据的方法
    var params = {
        "category_id": currentCid,
        "page": cur_page,

    };
    $.get("/article_list", params, function (resp) {
        if (resp.errno == 0){
            //请求成功
            total_page = resp.data.totalPage;  //设置总页数
            //清除已有数据
            if (cur_page == 1) {
                $(".article_list").html("");
            }
            //重新添加请求的数据
            for(var i=0;i<resp.data.articleList.length;i++){
                var article = resp.data.articleList[i];
                var content = '<div class="blogs">';
                content += '<figure><img src="'+ article.index_image_url +'"></figure>';
                content += '<ul>';
                content += '<h3><a href="/article/' + article.id +'">' + article.title + '</a></h3>';
                content += '<p>' + article.digest + '...</p>';
                content += '<p class="autor"><span class="lm f_l"><a href="#">' + article.category.name + '</a></span><span class="dtime f_l">' + article.create_time + '</span><span class="viewnum f_r">浏览（<a href="/">' + article.clicks + '</a>）</span><span class="pingl f_r">评论（' + article.comments_count + '）</span></p>';
                content += '</ul>';
                content += '</div>';
                $(".article_list").append(content);
            }
        }else{
            //请求失败
            alert(resp.errmsg)
        }
    })
}