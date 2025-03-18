db = db.getSiblingDB('factually_db');

db.createUser({
  user: "mongo_user",
  pwd: "mongo_pass",
  roles: [{ role: "readWrite", db: "factually_db" }]
});

// Helper function to generate a UUIDv4 string.
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
       var r = Math.random() * 16 | 0,
           v = c === 'x' ? r : (r & 0x3 | 0x8);
       return v.toString(16);
    });
}

var sources = {
  "theverge": {
      base_url: "https://www.theverge.com",
      url: "https://www.theverge.com/archives/{year}/{month}/{page}",
      article_selector: "duet--content-cards--content-card _1ufh7nr1 _1ufh7nr0 _1lkmsmo0",
      date_format: "%b %d",
      button_selector: null
  },
  "techcrunch": {
      base_url: "https://techcrunch.com",
      url: "https://techcrunch.com/{year}/{month}/page/{page}",
      article_selector: "loop-card loop-card--post-type-post loop-card--default loop-card--horizontal loop-card--wide loop-card--force-storyline-aspect-ratio",
      date_format: "%b %d, %Y",
      button_selector: null
  },
  "wired": {
      base_url: "https://es.wired.com",
      url: "https://es.wired.com/tag/inteligencia-artificial?page={page}",
      article_selector: "summary-item__content",
      date_format: "%d de %B de %Y",
      button_selector: null
  },
  "wsj": {
      base_url: "https://www.wsj.com",
      url: "https://www.wsj.com/news/archive/{year}/{month}/{day}?page={page}",
      article_selector: "WSJTheme--overflow-hidden--qJmlzHgO",
      date_format: "%d/%b/%Y",
      button_selector: null
  },
  "arstechnica": {
      base_url: "https://arstechnica.com",
      url: "https://arstechnica.com/{year}/page/{page}",
      article_selector: "flex flex-1 flex-col justify-between pl-3 sm:pl-5",
      date_format: "%m/%d/%Y",
      button_selector: "post-navigation-link"
  },
  "gizmodo": {
      base_url: "https://gizmodo.com",
      url: "https://gizmodo.com/latest/page/{page}",
      article_selector: "flex-1 self-center w-full",
      date_format: "%B %d, %Y",
      button_selector: null
  },
  "theregister": {
      base_url: "https://www.theregister.com",
      url: "https://www.theregister.com/Archive/{year}/{month}/{day}/",
      article_selector: "article_text_elements",
      date_format: "%d %b, %Y",
      button_selector: null
  }
};

for (var key in sources) {
    if (sources.hasOwnProperty(key)) {
        var source = sources[key];
        source.name = key;
        source._id = generateUUID();
        db.sources.insertOne(source);
    }
}
